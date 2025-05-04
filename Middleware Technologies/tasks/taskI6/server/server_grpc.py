import logging
from concurrent import futures

import grpc

from gen import item_pb2
from gen import item_pb2_grpc

items_db: dict[int, item_pb2.Item] = {}
item_id_counter = 0


class ItemService(item_pb2_grpc.ItemServiceServicer):
    def GetItems(
            self,
            request: item_pb2.GetItemsRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.GetItemsResponse:
        global items_db, item_id_counter

        logging.info("gRPC: GetItems called")
        if request.item_ids:
            items = [item for item in items_db.values() if item.id in request.item_ids]
            return item_pb2.GetItemsResponse(items=items)
        items = list(items_db.values())
        return item_pb2.GetItemsResponse(items=items)

    def AddItems(
            self,
            request: item_pb2.AddItemsRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.AddItemsResponse:
        global items_db, item_id_counter

        logging.info("gRPC: AddItems called")
        added_items: list[item_pb2.Item] = []
        for item_input in request.items:
            item_id_counter += 1
            item = item_pb2.Item(
                id=item_id_counter,
                name=item_input.name,
                value=item_input.value,
                details=item_input.details
            )
            items_db[item.id] = item
            added_items.append(item)
        return item_pb2.AddItemsResponse(items=added_items)

    def ClearItems(
            self,
            request: item_pb2.ClearItemsRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.ClearItemsResponse:
        global items_db, item_id_counter

        logging.info("gRPC: ClearItemList called")
        items_db.clear()
        item_id_counter = 0
        return item_pb2.ClearItemsResponse()


def serve(server_address: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    item_pb2_grpc.add_ItemServiceServicer_to_server(ItemService(), server)
    server.add_insecure_port(server_address)
    server.start()
    logging.info(f"gRPC: server started on {server_address}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("gRPC: server stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve("localhost:50051")
