import ray
import random
import asyncio
import traceback

# --- System Configuration ---
DEFAULT_REPLICATION_FACTOR = 2  # Desired number of replicas for each data chunk
DEFAULT_CHUNK_SIZE_BYTES = 128  # Size of each data chunk in bytes (small for demo)
NUM_STORAGE_NODES = 3  # Number of StorageNode actors to create


@ray.remote
class StorageNode:
    """
    A Ray actor representing a node that stores and serves data chunks.
    Each StorageNode maintains its own set of chunks.
    """

    def __init__(self, node_id: str):
        """
        Initializes the StorageNode.
        Args:
            node_id: A unique identifier for this storage node.
        """
        self.node_id = node_id
        self.chunks = {}  # In-memory store: chunk_id -> chunk_data (bytes)
        self._failed_state = False  # Internal flag to simulate node failure
        print(f"StorageNode {self.node_id}: Initialized.")

    def put_chunk(self, chunk_id: str, data: bytes) -> bool:
        """
        Stores a data chunk on this node.
        Args:
            chunk_id: The unique ID of the chunk.
            data: The byte content of the chunk.
        Returns:
            True if storage is successful.
        Raises:
            ray.exceptions.RayActorError: If the node is in a simulated failed state.
        """
        if self._failed_state:
            raise ray.exceptions.RayActorError(
                f"Node {self.node_id} is intentionally failed."
            )
        self.chunks[chunk_id] = data
        return True

    def get_chunk(self, chunk_id: str) -> bytes:
        """
        Retrieves a data chunk from this node.
        Args:
            chunk_id: The unique ID of the chunk.
        Returns:
            The byte content of the chunk.
        Raises:
            ray.exceptions.RayActorError: If the node is in a simulated failed state.
            KeyError: If the chunk_id is not found on this node.
        """
        if self._failed_state:
            raise ray.exceptions.RayActorError(
                f"Node {self.node_id} is intentionally failed."
            )
        if chunk_id not in self.chunks:
            # This indicates an inconsistency if NameNode thought this node had the chunk.
            # NameNode's re-replication logic should handle this scenario.
            raise KeyError(f"Chunk {chunk_id} not found on StorageNode {self.node_id}.")
        return self.chunks[chunk_id]

    def delete_chunk(self, chunk_id: str) -> bool:
        """
        Deletes a data chunk from this node. Idempotent.
        Args:
            chunk_id: The unique ID of the chunk.
        Returns:
            True, regardless of whether the chunk existed before deletion.
        Raises:
            ray.exceptions.RayActorError: If the node is in a simulated failed state.
        """
        if self._failed_state:
            raise ray.exceptions.RayActorError(
                f"Node {self.node_id} is intentionally failed."
            )
        if chunk_id in self.chunks:
            del self.chunks[chunk_id]
        return True

    def has_chunk(self, chunk_id: str) -> bool:
        """
        Checks if this node currently stores a specific chunk.
        Args:
            chunk_id: The unique ID of the chunk.
        Returns:
            True if the chunk exists on this node, False otherwise.
        Raises:
            ray.exceptions.RayActorError: If the node is in a simulated failed state.
        """
        if self._failed_state:
            raise ray.exceptions.RayActorError(
                f"Node {self.node_id} is intentionally failed."
            )
        return chunk_id in self.chunks

    def get_status(self) -> list:
        """
        Returns a list of chunk IDs currently stored on this node.
        Used by NameNode for its cluster status report.
        """
        if self._failed_state:
            raise ray.exceptions.RayActorError(
                f"Node {self.node_id} is intentionally failed."
            )
        return list(self.chunks.keys())

    def set_failure_status(self, fail: bool):
        """
        Simulates or recovers from node failure by setting an internal flag.
        When failed, most operations will raise RayActorError.
        Args:
            fail: If True, node enters a 'failed' state. If False, it becomes 'active'.
        """
        self._failed_state = fail
        status = "FAILED" if fail else "ACTIVE"
        print(f"StorageNode {self.node_id}: Status set to {status}.")
        # Note: This does not clear self.chunks. If a node recovers, it still has its old data.
        # The NameNode is responsible for managing metadata and re-replication.
        return f"Node {self.node_id} failure status set to {fail}"


@ray.remote
class NameNode:
    """
    A Ray actor acting as the central coordinator for the distributed storage system.
    It manages artifact metadata (chunk locations, artifact-to-chunk mapping),
    handles client requests (upload, download, delete, update),
    and orchestrates chunk replication and recovery from StorageNode failures.
    """

    def __init__(self, replication_factor: int, chunk_size_bytes: int):
        self.storage_nodes = {}  # node_id -> {'handle': ActorHandle, 'status': 'active'/'failed', 'id': str}
        self.artifact_metadata = {}  # artifact_name -> {'chunk_ids': list, 'chunk_locations': {chunk_id: [node_id]}}
        self.chunk_to_artifact_map = {}  # chunk_id -> artifact_name (for reverse lookup, aids cleanup)

        self.replication_factor = replication_factor
        self.chunk_size_bytes = chunk_size_bytes
        self.rereplication_lock = (
            asyncio.Lock()
        )  # Ensures only one re-replication cycle runs at a time

        print(
            f"NameNode: Initialized with replication_factor={replication_factor}, chunk_size={chunk_size_bytes} bytes."
        )

    def _generate_chunk_id(self, artifact_name: str, chunk_index: int) -> str:
        """Generates a consistent, unique ID for a chunk based on artifact name and index."""
        return f"{artifact_name}_chunk_{chunk_index}"

    def register_storage_node(
        self, node_id: str, node_handle: ray.actor.ActorHandle
    ) -> str:
        """Registers a StorageNode, making it available for storing chunks."""
        if node_id in self.storage_nodes:
            return f"NameNode: StorageNode {node_id} already registered."
        self.storage_nodes[node_id] = {
            "handle": node_handle,
            "status": "active",
            "id": node_id,
        }
        print(f"NameNode: Registered StorageNode {node_id}.")
        return f"NameNode: StorageNode {node_id} registered successfully."

    def _get_live_storage_nodes(self) -> list:
        """Returns a list of storage node details for nodes currently marked as 'active'."""
        return [
            details
            for details in self.storage_nodes.values()
            if details["status"] == "active"
        ]

    def _select_storage_nodes_for_chunk(
        self, num_nodes_needed: int, exclude_nodes_ids: list = None
    ) -> list:
        """
        Selects a random sample of live storage nodes to host a new chunk replica.
        Args:
            num_nodes_needed: The number of distinct storage nodes required.
            exclude_nodes_ids: A list of node_ids to exclude from selection (e.g., nodes already holding a replica).
        Returns:
            A list of storage node detail dictionaries.
        Raises:
            Exception: If not enough eligible live storage nodes are available.
        """
        if exclude_nodes_ids is None:
            exclude_nodes_ids = []

        live_nodes = self._get_live_storage_nodes()
        eligible_nodes = [
            node for node in live_nodes if node["id"] not in exclude_nodes_ids
        ]

        if len(eligible_nodes) < num_nodes_needed:
            raise Exception(
                f"Not enough eligible live storage nodes. Needed: {num_nodes_needed}, Available: {len(eligible_nodes)}, Excluded: {len(exclude_nodes_ids)}"
            )

        return random.sample(eligible_nodes, num_nodes_needed)

    async def _cleanup_failed_upload(
        self, artifact_name: str, partially_created_metadata: dict = None
    ):
        """
        Attempts to delete chunks that were partially uploaded before an error occurred.
        This is a best-effort cleanup.
        Args:
            artifact_name: The name of the artifact whose upload failed.
            partially_created_metadata: Metadata collected before the failure.
        """
        print(f"NameNode: Cleaning up partially uploaded artifact {artifact_name}.")
        metadata_to_use = self.artifact_metadata.get(
            artifact_name, partially_created_metadata
        )

        if not metadata_to_use:
            print(f"NameNode: No metadata found for {artifact_name} during cleanup.")
            return

        chunk_ids = metadata_to_use.get("chunk_ids", [])
        chunk_locations = metadata_to_use.get("chunk_locations", {})

        delete_tasks = []
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_to_artifact_map:
                del self.chunk_to_artifact_map[chunk_id]

            node_ids_for_chunk = chunk_locations.get(chunk_id, [])
            for node_id in node_ids_for_chunk:
                node_detail = self.storage_nodes.get(node_id)
                # Only attempt delete on nodes believed to be active
                if node_detail and node_detail["status"] == "active":
                    delete_tasks.append(
                        node_detail["handle"].delete_chunk.remote(chunk_id)
                    )

        if delete_tasks:
            await asyncio.gather(
                *delete_tasks, return_exceptions=True
            )  # Wait for cleanup deletes, ignore errors

        if artifact_name in self.artifact_metadata:
            del self.artifact_metadata[artifact_name]
        print(f"NameNode: Cleanup for {artifact_name} complete.")

    async def upload_artifact(self, artifact_name: str, content_str: str) -> str:
        """
        Handles artifact upload: chunks the content, selects storage nodes,
        writes chunks with replication, and updates metadata.
        """
        if artifact_name in self.artifact_metadata:
            return f"Error: Artifact '{artifact_name}' already exists. Use update_artifact."

        print(f"NameNode: Uploading artifact '{artifact_name}'...")
        content_bytes = content_str.encode("utf-8")
        chunks_data = [
            content_bytes[i : i + self.chunk_size_bytes]
            for i in range(0, len(content_bytes), self.chunk_size_bytes)
        ]

        if (
            not chunks_data and content_bytes
        ):  # content_bytes is not empty but chunks_data is
            return f"Error: Invalid chunk size ({self.chunk_size_bytes}) resulted in no chunks for non-empty artifact '{artifact_name}'."
        if not content_bytes:  # Handle empty artifact by creating one empty chunk
            chunks_data = [b""]

        temp_chunk_ids = []
        temp_chunk_locations = {}  # chunk_id -> [node_id]

        for i, chunk_data_bytes in enumerate(chunks_data):
            chunk_id = self._generate_chunk_id(artifact_name, i)
            temp_chunk_ids.append(chunk_id)

            placed_on_nodes_ids = []
            try:
                # Select distinct nodes for this chunk's replicas
                target_nodes_details = self._select_storage_nodes_for_chunk(
                    self.replication_factor
                )
            except Exception as e:
                await self._cleanup_failed_upload(
                    artifact_name,
                    {
                        "chunk_ids": temp_chunk_ids,
                        "chunk_locations": temp_chunk_locations,
                    },
                )
                return f"Error uploading '{artifact_name}': Could not select nodes for chunk {chunk_id}. {e}"

            # Asynchronously put chunk to selected nodes
            put_tasks = [
                node_detail["handle"].put_chunk.remote(chunk_id, chunk_data_bytes)
                for node_detail in target_nodes_details
            ]
            results = await asyncio.gather(*put_tasks, return_exceptions=True)

            for idx, result in enumerate(results):
                node_detail = target_nodes_details[idx]
                if isinstance(result, Exception):
                    print(
                        f"Warning: Failed to put chunk {chunk_id} on node {node_detail['id']}. Error: {result}"
                    )
                    await self._mark_node_failed(
                        node_detail["id"]
                    )  # Mark node and trigger re-replication later
                else:
                    placed_on_nodes_ids.append(node_detail["id"])

            if (
                not placed_on_nodes_ids
            ):  # Critical: chunk couldn't be placed on any node
                await self._cleanup_failed_upload(
                    artifact_name,
                    {
                        "chunk_ids": temp_chunk_ids,
                        "chunk_locations": temp_chunk_locations,
                    },
                )
                return f"Error: Failed to store chunk {chunk_id} of '{artifact_name}' on ANY node. Upload aborted."

            temp_chunk_locations[chunk_id] = placed_on_nodes_ids
            if len(placed_on_nodes_ids) < self.replication_factor:
                print(
                    f"Warning: Chunk {chunk_id} for '{artifact_name}' has only {len(placed_on_nodes_ids)} replicas (desired {self.replication_factor}). Re-replication will be attempted."
                )

        # All chunks processed, commit metadata
        self.artifact_metadata[artifact_name] = {
            "chunk_ids": temp_chunk_ids,
            "chunk_locations": temp_chunk_locations,
        }
        for cid in temp_chunk_ids:
            self.chunk_to_artifact_map[cid] = artifact_name

        print(
            f"NameNode: Artifact '{artifact_name}' uploaded successfully with {len(temp_chunk_ids)} chunks."
        )
        # Asynchronously trigger a re-replication check in case some chunks are under-replicated from the start
        asyncio.create_task(self._initiate_rereplication())
        return f"Artifact '{artifact_name}' uploaded successfully."

    async def get_artifact(self, artifact_name: str) -> str:
        """
        Retrieves an artifact by fetching its chunks from available StorageNodes
        and reassembling them.
        """
        if artifact_name not in self.artifact_metadata:
            return f"Error: Artifact '{artifact_name}' not found."

        print(f"NameNode: Retrieving artifact '{artifact_name}'...")
        metadata = self.artifact_metadata[artifact_name]
        chunk_ids = metadata["chunk_ids"]

        artifact_content_parts = []

        for chunk_id in chunk_ids:
            # Fetch current locations; re-replication might have changed them
            chunk_locations_for_id = metadata["chunk_locations"].get(chunk_id, [])
            node_ids_to_try = list(chunk_locations_for_id)
            random.shuffle(
                node_ids_to_try
            )  # Try nodes in random order for basic load distribution

            chunk_data_bytes = None
            fetched_successfully = False

            for node_id in node_ids_to_try:
                node_detail = self.storage_nodes.get(node_id)
                if node_detail and node_detail["status"] == "active":
                    try:
                        chunk_data_bytes = await node_detail["handle"].get_chunk.remote(
                            chunk_id
                        )
                        fetched_successfully = True
                        break  # Got the chunk
                    except ray.exceptions.RayActorError:  # Node failed during call
                        print(
                            f"Warning: Node {node_id} failed while getting chunk {chunk_id}. Marking as failed."
                        )
                        await self._mark_node_failed(node_id)
                    except KeyError:  # Chunk not on this node, though metadata said so (inconsistency)
                        print(
                            f"Warning: Chunk {chunk_id} not found on node {node_id} (metadata inconsistency). Removing from this chunk's locations."
                        )
                        if node_id in metadata["chunk_locations"].get(
                            chunk_id, []
                        ):  # Defensive check
                            metadata["chunk_locations"][chunk_id].remove(node_id)
                        asyncio.create_task(
                            self._initiate_rereplication()
                        )  # May now be under-replicated
                    except Exception as e:
                        print(
                            f"Warning: Unexpected error getting chunk {chunk_id} from {node_id}: {e}"
                        )

            if not fetched_successfully or chunk_data_bytes is None:
                asyncio.create_task(
                    self._initiate_rereplication()
                )  # Attempt to fix missing/under-replicated chunk
                return f"Error: Failed to retrieve chunk {chunk_id} for artifact '{artifact_name}'. Artifact might be corrupted or temporarily unavailable. Re-replication initiated. Try again later."

            artifact_content_parts.append(chunk_data_bytes)

        return b"".join(artifact_content_parts).decode("utf-8")

    async def delete_artifact(self, artifact_name: str) -> str:
        """Deletes an artifact: removes its metadata and instructs StorageNodes to delete chunks."""
        if artifact_name not in self.artifact_metadata:
            return f"Error: Artifact '{artifact_name}' not found."

        print(f"NameNode: Deleting artifact '{artifact_name}'...")
        metadata = self.artifact_metadata.pop(
            artifact_name
        )  # Remove from metadata first
        chunk_ids = metadata["chunk_ids"]
        chunk_locations = metadata["chunk_locations"]

        delete_tasks = []
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_to_artifact_map:
                del self.chunk_to_artifact_map[chunk_id]

            node_ids_for_chunk = chunk_locations.get(chunk_id, [])
            for node_id in node_ids_for_chunk:
                node_detail = self.storage_nodes.get(node_id)
                if node_detail and node_detail["status"] == "active":
                    delete_tasks.append(
                        node_detail["handle"].delete_chunk.remote(chunk_id)
                    )

        if delete_tasks:
            # Wait for delete operations, but don't let one failure stop others.
            # Errors are logged; a more robust system might retry or flag problematic nodes.
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Warning: A delete_chunk operation failed: {result}")

        print(f"NameNode: Artifact '{artifact_name}' deleted.")
        return f"Artifact '{artifact_name}' deleted successfully."

    async def update_artifact(self, artifact_name: str, new_content_str: str) -> str:
        """
        Updates an existing artifact. Implemented as a delete-then-upload operation.
        This is not atomic; if the upload phase fails, the artifact might be partially
        deleted or in an inconsistent state.
        """
        if artifact_name not in self.artifact_metadata:
            return f"Error: Artifact '{artifact_name}' not found. Use upload_artifact to create."

        print(f"NameNode: Updating artifact '{artifact_name}'...")
        # Delete the old version first
        delete_result = await self.delete_artifact(artifact_name)

        if "Error" in delete_result and "not found" not in delete_result:
            print(
                f"Warning during update: Deletion of old '{artifact_name}' reported: {delete_result}"
            )
            # Proceeding with upload, but the system might have orphaned chunks from the old version.

        # Upload the new version
        upload_result = await self.upload_artifact(artifact_name, new_content_str)
        if "Error" in upload_result:
            return f"Error updating '{artifact_name}': Upload phase failed. {upload_result}. Artifact may be in an inconsistent state."
        return f"Artifact '{artifact_name}' updated successfully."

    async def list_artifacts(self) -> str:
        """Returns a string listing all stored artifacts and their chunk IDs."""
        if not self.artifact_metadata:
            return "No artifacts stored."

        output = ["Stored Artifacts:"]
        for name, meta in self.artifact_metadata.items():
            output.append(f"- Artifact: {name}")
            output.append(f"  Chunks ({len(meta['chunk_ids'])}): {meta['chunk_ids']}")
        return "\n".join(output)

    async def _mark_node_failed(self, node_id: str):
        """
        Internal method to mark a storage node as 'failed' in NameNode's records
        and trigger an asynchronous re-replication check.
        """
        if (
            node_id in self.storage_nodes
            and self.storage_nodes[node_id]["status"] == "active"
        ):
            self.storage_nodes[node_id]["status"] = "failed"
            print(f"NameNode: StorageNode {node_id} marked as FAILED.")
            # Trigger re-replication non-blockingly
            asyncio.create_task(self._initiate_rereplication())
        elif node_id not in self.storage_nodes:
            print(f"NameNode: Attempted to mark unknown node {node_id} as failed.")

    async def _check_replication_and_get_deficient_chunks(self) -> dict:
        """
        Scans all artifacts and their chunks to identify any that are under-replicated
        or have lost all replicas, based on current StorageNode statuses.
        It also updates the `chunk_locations` in metadata to reflect only live nodes.
        Returns:
            A dictionary of deficient_chunk_id -> details.
        """
        deficient_chunks = {}
        # Iterate over a copy of items, as metadata might be modified (e.g., artifact deleted)
        for artifact_name, meta in list(self.artifact_metadata.items()):
            if artifact_name not in self.artifact_metadata:
                continue  # Artifact deleted concurrently

            for chunk_id in list(
                meta["chunk_locations"].keys()
            ):  # Iterate copy of keys
                current_node_ids_for_chunk = meta["chunk_locations"].get(chunk_id, [])
                live_node_ids_for_this_chunk = []
                data_source_handle = None  # A handle to a live node holding the chunk

                for node_id in current_node_ids_for_chunk:
                    node_detail = self.storage_nodes.get(node_id)
                    if node_detail and node_detail["status"] == "active":
                        live_node_ids_for_this_chunk.append(node_id)
                        if (
                            not data_source_handle
                        ):  # Pick first live node as potential data source
                            data_source_handle = node_detail["handle"]

                # Update metadata to reflect only currently live nodes for this chunk
                meta["chunk_locations"][chunk_id] = live_node_ids_for_this_chunk
                num_live_replicas = len(live_node_ids_for_this_chunk)

                if num_live_replicas < self.replication_factor:
                    deficient_chunks[chunk_id] = {
                        "artifact_name": artifact_name,
                        "live_replicas": num_live_replicas,
                        "expected_replicas": self.replication_factor,
                        "live_node_ids": live_node_ids_for_this_chunk,
                        "data_source_handle": data_source_handle
                        if num_live_replicas > 0
                        else None,
                    }
                    if (
                        num_live_replicas == 0 and current_node_ids_for_chunk
                    ):  # Had replicas, now all presumed dead
                        print(
                            f"CRITICAL: Chunk {chunk_id} of artifact {artifact_name} has NO live replicas. Data may be lost!"
                        )
                    elif num_live_replicas > 0:
                        print(
                            f"INFO: Chunk {chunk_id} (Artifact: {artifact_name}) is under-replicated: {num_live_replicas}/{self.replication_factor}."
                        )
        return deficient_chunks

    async def _initiate_rereplication(self):
        """
        Core background process for maintaining data redundancy.
        Identifies under-replicated chunks and attempts to create new replicas
        on other available StorageNodes. Uses a lock to prevent concurrent runs.
        """
        if self.rereplication_lock.locked():
            print(
                "NameNode: Re-replication is already in progress. Skipping new initiation."
            )
            return

        async with self.rereplication_lock:
            print("NameNode: Initiating re-replication check...")
            deficient_chunks = await self._check_replication_and_get_deficient_chunks()

            if not deficient_chunks:
                print("NameNode: No chunks require re-replication at this time.")
                return

            print(
                f"NameNode: Found {len(deficient_chunks)} chunks needing attention for re-replication."
            )

            for chunk_id, details in deficient_chunks.items():
                artifact_name = details["artifact_name"]
                if (
                    artifact_name not in self.artifact_metadata
                ):  # Artifact might have been deleted
                    print(
                        f"NameNode: Artifact {artifact_name} for chunk {chunk_id} no longer exists. Skipping re-replication."
                    )
                    continue

                num_live_replicas = details["live_replicas"]
                num_needed = self.replication_factor - num_live_replicas
                data_source_handle = details["data_source_handle"]
                current_live_node_ids = details["live_node_ids"]

                if num_needed <= 0:  # Meets factor or data is lost (0 live replicas)
                    if num_live_replicas == 0:  # Data lost
                        print(
                            f"NameNode: Cannot re-replicate chunk {chunk_id} (Artifact: {artifact_name}) as it has no live source."
                        )
                    continue

                if not data_source_handle:  # Should not happen if num_live_replicas > 0
                    print(
                        f"Error: No data source handle for under-replicated chunk {chunk_id} (Artifact: {artifact_name}). Skipping."
                    )
                    continue

                print(
                    f"NameNode: Re-replicating chunk {chunk_id} (Artifact: {artifact_name}). Needs {num_needed} more replicas."
                )

                chunk_data_bytes = None
                try:
                    # Fetch chunk data from a live source
                    chunk_data_bytes = await data_source_handle.get_chunk.remote(
                        chunk_id
                    )
                except Exception as e:
                    print(
                        f"Error: Could not retrieve chunk {chunk_id} from source for re-replication: {e}. Source node might be failing."
                    )
                    if isinstance(
                        e, ray.exceptions.RayActorError
                    ):  # Source actor itself failed
                        for (
                            nid,
                            ndetail,
                        ) in self.storage_nodes.items():  # Find node_id to mark
                            if ndetail["handle"] == data_source_handle:
                                await self._mark_node_failed(nid)
                                break
                    continue  # Skip this chunk for now

                if (
                    chunk_data_bytes is None
                ):  # Should be caught by exception above if get_chunk fails
                    print(
                        f"Error: Retrieved None for chunk {chunk_id} data from source. Skipping re-replication."
                    )
                    continue

                try:
                    # Select new distinct nodes for the new replicas
                    new_target_nodes_details = self._select_storage_nodes_for_chunk(
                        num_needed, exclude_nodes_ids=current_live_node_ids
                    )
                except Exception as e:
                    print(
                        f"Warning: Could not select enough new distinct nodes for re-replicating chunk {chunk_id}: {e}. Will try later."
                    )
                    continue

                # Put the chunk data onto the newly selected nodes
                put_tasks_rereplicate = [
                    node_detail["handle"].put_chunk.remote(chunk_id, chunk_data_bytes)
                    for node_detail in new_target_nodes_details
                ]
                results_rereplicate = await asyncio.gather(
                    *put_tasks_rereplicate, return_exceptions=True
                )

                for idx, result in enumerate(results_rereplicate):
                    node_detail = new_target_nodes_details[idx]
                    if isinstance(result, Exception):
                        print(
                            f"Warning: Node {node_detail['id']} failed during re-replication of chunk {chunk_id}. Error: {result}"
                        )
                        await self._mark_node_failed(node_detail["id"])
                    else:
                        # Successfully re-replicated, update metadata
                        # Ensure artifact and chunk still exist in metadata and avoid adding duplicate node_id
                        if (
                            artifact_name in self.artifact_metadata
                            and chunk_id
                            in self.artifact_metadata[artifact_name]["chunk_locations"]
                            and node_detail["id"]
                            not in self.artifact_metadata[artifact_name][
                                "chunk_locations"
                            ][chunk_id]
                        ):
                            self.artifact_metadata[artifact_name]["chunk_locations"][
                                chunk_id
                            ].append(node_detail["id"])
                            print(
                                f"NameNode: Successfully re-replicated chunk {chunk_id} to node {node_detail['id']}."
                            )
                        elif node_detail["id"] in self.artifact_metadata.get(
                            artifact_name, {}
                        ).get("chunk_locations", {}).get(chunk_id, []):
                            # This case handles if, due to timing, the node was already added by another concurrent check (less likely with lock)
                            print(
                                f"NameNode: Chunk {chunk_id} already listed on node {node_detail['id']}. No metadata update needed for this replica."
                            )
                        else:
                            # Artifact or chunk might have been deleted during this async operation
                            print(
                                f"NameNode: Artifact {artifact_name} or chunk {chunk_id} was removed/changed during re-replication. New replica on {node_detail['id']} might be orphaned."
                            )

            print("NameNode: Re-replication cycle finished.")

    async def get_cluster_status(self) -> str:
        """Provides a comprehensive status report of the cluster, including node health and artifact replication."""
        output = ["Cluster Status:"]
        output.append(
            f"NameNode Configuration: Replication Factor={self.replication_factor}, Chunk Size={self.chunk_size_bytes} bytes"
        )
        output.append(f"Total Storage Nodes Registered: {len(self.storage_nodes)}")

        live_nodes_count = 0
        failed_nodes_count = 0

        storage_node_statuses_tasks_map = {}
        active_node_ids_for_status = []

        for node_id, details in self.storage_nodes.items():
            if details["status"] == "active":
                live_nodes_count += 1
                active_node_ids_for_status.append(node_id)
                storage_node_statuses_tasks_map[node_id] = details[
                    "handle"
                ].get_status.remote()
            else:
                failed_nodes_count += 1

        output.append(f"Live Storage Nodes: {live_nodes_count}")
        output.append(f"Failed Storage Nodes: {failed_nodes_count}")

        output.append("\nStorage Node Chunk Details:")
        if storage_node_statuses_tasks_map:
            tasks_in_order = [
                storage_node_statuses_tasks_map[nid]
                for nid in active_node_ids_for_status
            ]
            gathered_statuses = await asyncio.gather(
                *tasks_in_order, return_exceptions=True
            )

            for i, node_id in enumerate(active_node_ids_for_status):
                result = gathered_statuses[i]
                if isinstance(result, Exception):
                    output.append(
                        f"  Node {node_id} (active) - FAILED to get status. Marking as failed. Error: {result}"
                    )
                    await self._mark_node_failed(node_id)
                else:
                    node_chunk_list = result  # List of chunk_ids on this node
                    # Display only a few chunk_ids for brevity if many are present
                    display_chunks = str(node_chunk_list[:5]) + (
                        "..." if len(node_chunk_list) > 5 else ""
                    )
                    output.append(
                        f"  Node {node_id} (active) stores {len(node_chunk_list)} chunks: {display_chunks}"
                    )
        else:
            output.append("  No active storage nodes to query.")

        output.append("\nOverall Artifact Distribution & Replication Health:")
        deficient_chunks = await self._check_replication_and_get_deficient_chunks()

        if not self.artifact_metadata:
            output.append("  No artifacts currently stored.")
        else:
            for artifact_name, meta in self.artifact_metadata.items():
                output.append(
                    f"- Artifact: '{artifact_name}' ({len(meta['chunk_ids'])} chunks)"
                )
                for chunk_id in meta["chunk_ids"]:
                    live_nodes = meta["chunk_locations"].get(chunk_id, [])
                    status_msg = "OK"
                    num_live = len(live_nodes)
                    if chunk_id in deficient_chunks:
                        if deficient_chunks[chunk_id]["live_replicas"] == 0:
                            status_msg = "CRITICAL - DATA LOST!"
                        else:
                            status_msg = f"UNDER-REPLICATED ({num_live}/{self.replication_factor})"
                    output.append(
                        f"    Chunk: {chunk_id}, Live Replicas: {num_live}/{self.replication_factor} on {live_nodes} [{status_msg}]"
                    )

        if deficient_chunks:
            output.append(
                "\nWARNING: Some chunks require attention (under-replicated or lost). Re-replication might be in progress or needed."
            )
        else:
            output.append(
                "\nAll stored chunks (tracked by NameNode) appear to meet the desired replication factor based on current node statuses."
            )

        return "\n".join(output)

    async def simulate_node_failure(self, node_id_to_fail: str) -> str:
        """Simulates a StorageNode failure for testing purposes."""
        if node_id_to_fail not in self.storage_nodes:
            return f"Error: Node {node_id_to_fail} not found."

        node_detail = self.storage_nodes[node_id_to_fail]
        if node_detail["status"] == "failed":
            return f"Node {node_id_to_fail} is already marked as failed."

        try:
            # Instruct the StorageNode actor to enter a failed state
            await node_detail["handle"].set_failure_status.remote(True)
            # Update NameNode's record and trigger re-replication
            await self._mark_node_failed(node_id_to_fail)
            return f"Simulated failure for node {node_id_to_fail}. Re-replication process initiated."
        except Exception as e:
            # If instructing the node fails (e.g., it's already unresponsive), still mark it failed in NameNode
            await self._mark_node_failed(node_id_to_fail)
            return f"Error instructing node {node_id_to_fail} to fail, but marked as failed in NameNode: {e}"

    async def recover_node(self, node_id_to_recover: str) -> str:
        """Simulates a StorageNode recovery."""
        if node_id_to_recover not in self.storage_nodes:
            return f"Error: Node {node_id_to_recover} not found for recovery."

        node_detail = self.storage_nodes[node_id_to_recover]
        try:
            # Instruct the StorageNode actor to exit failed state
            await node_detail["handle"].set_failure_status.remote(False)
            if node_detail["status"] == "failed":  # If it was marked failed
                node_detail["status"] = "active"
                print(
                    f"NameNode: StorageNode {node_id_to_recover} marked as ACTIVE again."
                )
                # Trigger re-replication check; this node might now take some load or balance existing data
                asyncio.create_task(self._initiate_rereplication())
                return f"Node {node_id_to_recover} recovered and marked active. Re-replication check triggered."
            return f"Node {node_id_to_recover} was already active."
        except Exception as e:
            # If recovery instruction fails, status remains unchanged (likely 'failed')
            return f"Error recovering node {node_id_to_recover}: {e}. Node status in NameNode unchanged."


# --- Main Client / Demo Logic ---
async def demo_operations(name_node_handle, storage_node_handles_map):
    """Runs a sequence of operations to demonstrate the storage system's capabilities."""
    print("\n--- Starting Distributed Artifact Storage Demo ---")

    print("\n=== Initial Cluster Status ===")
    print(await name_node_handle.get_cluster_status.remote())

    # 1. Upload an artifact, list the status
    print("\n=== Test 1: Upload Artifact 'doc1' ===")
    artifact1_content = (
        "This is the first document. It is a test document for our Ray distributed storage system."
        * 5
    )
    print(f"Uploading 'doc1' (length: {len(artifact1_content)} bytes)...")
    print(await name_node_handle.upload_artifact.remote("doc1", artifact1_content))
    await asyncio.sleep(
        1
    )  # Allow time for async tasks (like initial re-replication check) and logging
    print(await name_node_handle.get_cluster_status.remote())
    print(await name_node_handle.list_artifacts.remote())

    # Upload another artifact
    print("\n=== Upload Artifact 'doc2' ===")
    artifact2_content = "A shorter document, number two." * 3
    print(f"Uploading 'doc2' (length: {len(artifact2_content)} bytes)...")
    print(await name_node_handle.upload_artifact.remote("doc2", artifact2_content))
    await asyncio.sleep(1)
    print(await name_node_handle.get_cluster_status.remote())

    # 2. Get an artifact, list the status
    print("\n=== Test 2: Get Artifact 'doc1' ===")
    retrieved_doc1 = await name_node_handle.get_artifact.remote("doc1")
    if "Error" in retrieved_doc1:
        print(f"Error retrieving doc1: {retrieved_doc1}")
    else:
        print(
            f"Retrieved 'doc1' successfully. Matches original: {retrieved_doc1 == artifact1_content}"
        )
    print(await name_node_handle.get_cluster_status.remote())

    # 3. Update an artifact, list the status
    print("\n=== Test 3: Update Artifact 'doc2' ===")
    updated_artifact2_content = (
        "This is the NEW and UPDATED content for document two. It's much better now!"
        * 2
    )
    print(f"Updating 'doc2' (new length: {len(updated_artifact2_content)} bytes)...")
    print(
        await name_node_handle.update_artifact.remote("doc2", updated_artifact2_content)
    )
    await asyncio.sleep(1)  # Allow time for delete and re-upload async tasks
    retrieved_doc2_updated = await name_node_handle.get_artifact.remote("doc2")
    if "Error" in retrieved_doc2_updated:
        print(f"Error retrieving updated doc2: {retrieved_doc2_updated}")
    else:
        print(
            f"Retrieved updated 'doc2' successfully. Matches new content: {retrieved_doc2_updated == updated_artifact2_content}"
        )
    print(await name_node_handle.get_cluster_status.remote())

    # 4. Simulate Node Failure
    if not storage_node_handles_map:
        print("No storage nodes to fail. Skipping failure test.")
    else:
        # Fail the first storage node in the map for predictability in the demo
        target_node_to_fail_id = list(storage_node_handles_map.keys())[0]
        print(f"\n=== Test 4: Simulate Failure of Node '{target_node_to_fail_id}' ===")
        print(
            await name_node_handle.simulate_node_failure.remote(target_node_to_fail_id)
        )
        print(
            "Waiting a bit for re-replication to potentially kick in (check NameNode logs)..."
        )
        await asyncio.sleep(5)  # Give re-replication time to process
        print("\n--- Status After Node Failure and Potential Re-replication ---")
        print(await name_node_handle.get_cluster_status.remote())

        print("\n--- Attempting to Get 'doc1' After Node Failure ---")
        retrieved_doc1_after_failure = await name_node_handle.get_artifact.remote(
            "doc1"
        )
        if "Error" in retrieved_doc1_after_failure:
            print(
                f"Error retrieving doc1 after failure: {retrieved_doc1_after_failure}"
            )
        else:
            print(
                f"Retrieved 'doc1' successfully after node failure. Matches original: {retrieved_doc1_after_failure == artifact1_content}"
            )

    # 5. Delete an artifact, list the status
    print("\n=== Test 5: Delete Artifact 'doc1' ===")
    print(await name_node_handle.delete_artifact.remote("doc1"))
    print(await name_node_handle.get_cluster_status.remote())
    print(await name_node_handle.list_artifacts.remote())

    # Attempt to get the deleted artifact (should fail)
    print(await name_node_handle.get_artifact.remote("doc1"))

    # 6. Recover Node
    if storage_node_handles_map:
        target_node_to_recover_id = list(storage_node_handles_map.keys())[
            0
        ]  # The node previously failed
        if (
            target_node_to_recover_id in storage_node_handles_map
        ):  # Check if key is still valid
            print(f"\n=== Test 6: Recover Node '{target_node_to_recover_id}' ===")
            print(await name_node_handle.recover_node.remote(target_node_to_recover_id))
            await asyncio.sleep(2)  # Allow time for recovery and re-replication check
            print("\n--- Status After Node Recovery ---")
            print(await name_node_handle.get_cluster_status.remote())
            # Note: The recovered node might still show its old chunks if queried directly,
            # but NameNode's metadata is the source of truth for active data.
        else:
            print(
                f"Node {target_node_to_recover_id} no longer in map, skipping recovery test."
            )

    print("\n--- Distributed Artifact Storage Demo Finished ---")


if __name__ == "__main__":
    # Initialize Ray. `ignore_reinit_error` is useful for iterative development.
    if ray.is_initialized():
        ray.shutdown()
    ray.init(ignore_reinit_error=True)

    # Ray usually prints the dashboard URL upon init. This is a fallback reminder.
    print(f"Ray Dashboard typically at: http://127.0.0.1:8265")
    # The "detached actor in an anonymous namespace" message is informational.
    # For this script, actors are used immediately. For inter-script communication,
    # a named namespace would be `ray.init(namespace="my_app_namespace")`.

    name_node_actor_handle = None
    storage_nodes_map_instance = {}

    registration_obj_refs = []  # To hold ObjectRefs for registration calls

    try:
        # Create StorageNode actors
        for i in range(NUM_STORAGE_NODES):
            node_id = f"storage_node_{i}"
            # Using unique names for actors can be helpful for debugging in the Ray dashboard.
            # `lifetime="detached"` means the actor persists even if the handle goes out of scope in the driver,
            # until ray.shutdown() or explicitly killed. Useful for service-like actors.
            handle = StorageNode.options(
                name=f"StorageNode_{node_id}", lifetime="detached"
            ).remote(node_id=node_id)
            storage_nodes_map_instance[node_id] = handle
        print(f"Created {NUM_STORAGE_NODES} StorageNode actors.")

        # Create NameNode actor
        name_node_actor_handle = NameNode.options(
            name="NameNode", lifetime="detached"
        ).remote(
            replication_factor=DEFAULT_REPLICATION_FACTOR,
            chunk_size_bytes=DEFAULT_CHUNK_SIZE_BYTES,
        )
        print("NameNode actor created.")

        # Collect ObjectRefs for StorageNode registration calls
        for node_id, handle in storage_nodes_map_instance.items():
            registration_obj_refs.append(
                name_node_actor_handle.register_storage_node.remote(node_id, handle)
            )

        # Define the main async function to run all asynchronous setup and demo operations
        async def run_all_async_operations():
            # Wait for all StorageNodes to register with the NameNode
            registration_results = await asyncio.gather(*registration_obj_refs)
            for res in registration_results:
                print(res)  # Print registration confirmation messages

            # Run the demonstration operations
            await demo_operations(name_node_actor_handle, storage_nodes_map_instance)

        # Execute the main async operations block
        asyncio.run(run_all_async_operations())

    except Exception as e:
        print(f"An error occurred in the main execution block: {e}")
        traceback.print_exc()  # Print full traceback for debugging
    finally:
        print("Shutting down Ray...")
        ray.shutdown()
        print("Ray shutdown complete.")
