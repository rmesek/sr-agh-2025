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

        ######### clear items #########
        try:
            stub.ClearItems(item_pb2.ClearItemsRequest())
        except grpc.RpcError as e:
            logging.error(f"gRPC: ClearItems failed with error: {e}")
            return
        ###############################

        ########## add items ##########
        new_items = [
            item_pb2.ItemInput(name=f"Item {i}", value=10.0 * i, details=f"Details for item {i}")
            for i in range(item_number)
        ]
        add_request = item_pb2.AddItemsRequest(items=new_items)
        try:
            start_time = time.perf_counter_ns()
            stub.AddItems(add_request)
            stop_time = time.perf_counter_ns()
        except grpc.RpcError as e:
            logging.error(f"gRPC: AddItem failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"gRPC: Added items ({len(add_request.items)}) in {time_ms:.4f} ms")
        add_request_size = add_request.ByteSize()
        logging.info(f"gRPC: add_request size: {add_request_size} bytes")
        ###############################

        ########## get items ##########
        try:
            start_time = time.perf_counter_ns()
            get_response = stub.GetItems(item_pb2.GetItemsRequest())
            stop_time = time.perf_counter_ns()
        except grpc.RpcError as e:
            logging.error(f"gRPC: GetItems failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"gRPC: Retrieved items ({len(get_response.items)}) in {time_ms:.4f} ms")
        get_response_size = get_response.ByteSize()
        logging.info(f"gRPC: get_response size: {get_response_size} bytes")
        ###############################

    stop_total_time = time.perf_counter_ns()
    time_ms = (stop_total_time - start_total_time) / 1_000_000
    logging.info(f"gRPC: Total time: {time_ms:.4f} ms")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    benchmark("localhost:50051")
