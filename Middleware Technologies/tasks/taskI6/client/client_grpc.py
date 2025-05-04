import logging
import time

import grpc

from gen import item_pb2
from gen import item_pb2_grpc


def benchmark(server_address: str, item_number: int = 1000):
    logging.info(f"gRPC: benchmark {server_address}")

    start_total_time = time.perf_counter_ns()
    with grpc.insecure_channel(server_address) as channel:
        stub = item_pb2_grpc.ItemServiceStub(channel)
        stop_time = time.perf_counter_ns()
        time_ms = (stop_time - start_total_time) / 1_000_000
        logging.info(f"gRPC: Channel created in {time_ms:.4f} ms")

        # clear items
        try:
            stub.ClearItemList(item_pb2.ClearItemListRequest())
        except grpc.RpcError as e:
            logging.error(f"gRPC: ClearItemList failed with error: {e}")
            return

        # add items
        item_requests = [
            item_pb2.AddItemRequest(
                name=f"Item {i}",
                value=10.0 * i,
                details=f"Details for item {i}"
            ) for i in range(item_number)
        ]
        try:
            start_time = time.perf_counter_ns()
            for item_request in item_requests:
                stub.AddItem(item_request)
            stop_time = time.perf_counter_ns()
        except grpc.RpcError as e:
            logging.error(f"gRPC: AddItem failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"gRPC: Added items ({len(item_requests)}) in {time_ms:.4f} ms")
        item_requests_size = sum(item_request.ByteSize() for item_request in item_requests)
        logging.info(f"gRPC: Sum of item_requests size: {item_requests_size} bytes")

        # get item list
        try:
            start_time = time.perf_counter_ns()
            item_list_response = stub.GetItemList(item_pb2.GetItemListRequest())
            stop_time = time.perf_counter_ns()
        except grpc.RpcError as e:
            logging.error(f"gRPC: GetItemList failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"gRPC: Retrieved item_list ({len(item_list_response.items)}) in {time_ms:.4f} ms")
        item_list_response_size = item_list_response.ByteSize()
        logging.info(f"gRPC: item_list_response size: {item_list_response_size} bytes")

        # get item by id
        try:
            retrieved_items: list[item_pb2.Item] = []
            start_time = time.perf_counter_ns()
            for i in range(1, item_number + 1):
                retrieved_items.append(stub.GetItem(item_pb2.GetItemRequest(id=i)))
            stop_time = time.perf_counter_ns()
        except grpc.RpcError as e:
            logging.error(f"gRPC: GetItem failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"gRPC: Retrieved items ({len(retrieved_items)}) in {time_ms:.4f} ms")
        retrieved_items_size = sum(item.ByteSize() for item in retrieved_items)
        logging.info(f"gRPC: Sum of retrieved_items size: {retrieved_items_size} bytes")

    stop_total_time = time.perf_counter_ns()
    time_ms = (stop_total_time - start_total_time) / 1_000_000
    logging.info(f"gRPC: Total time: {time_ms:.4f} ms")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    benchmark("localhost:50051")
