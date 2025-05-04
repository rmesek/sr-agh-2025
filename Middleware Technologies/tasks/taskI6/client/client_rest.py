import logging
import time

import requests


def benchmark(server_address: str, item_number: int = 1000):
    base_url = f"http://{server_address}"
    logging.info(f"REST: benchmark {server_address}")

    start_total_time = time.perf_counter_ns()
    with requests.Session() as s:
        stop_time = time.perf_counter_ns()
        time_ms = (stop_time - start_total_time) / 1_000_000
        logging.info(f"REST: Session created in {time_ms:.4f} ms")

        # clear items
        try:
            s.delete(f"{base_url}/items")
        except requests.RequestException as e:
            logging.error(f"REST: ClearItemList failed with error: {e}")
            return

        # add items
        item_requests = [
            {
                "name": f"Item {i}",
                "value": 10.0 * i,
                "details": f"Details for item {i}"
            } for i in range(item_number)
        ]
        try:
            start_time = time.perf_counter_ns()
            for item_request in item_requests:
                s.post(f"{base_url}/items", json=item_request)
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"REST: AddItem failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"REST: Added items ({len(item_requests)}) in {time_ms:.4f} ms")
        item_requests_size = sum(len(str(item_request).encode("utf-8")) for item_request in item_requests)
        logging.info(f"REST: Sum of item_requests size: {item_requests_size} bytes")

        # get item list
        try:
            start_time = time.perf_counter_ns()
            item_list_response = s.get(f"{base_url}/items")
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"REST: GetItemList failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"REST: Retrieved item_list ({len(item_list_response.json())}) in {time_ms:.4f} ms")
        item_list_response_size = len(item_list_response.content)
        logging.info(f"REST: item_list_response size: {item_list_response_size} bytes")

        # get item by id
        try:
            retrieved_items: list[dict] = []
            start_time = time.perf_counter_ns()
            for i in range(1, item_number + 1):
                retrieved_items.append(s.get(f"{base_url}/items/{i}").json())
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"REST: GetItem failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"REST: Retrieved items ({len(retrieved_items)}) in {time_ms:.4f} ms")
        retrieved_items_size = sum(len(str(item).encode("utf-8")) for item in retrieved_items)
        logging.info(f"REST: Sum of retrieved_items size: {retrieved_items_size} bytes")

    stop_total_time = time.perf_counter_ns()
    time_ms = (stop_total_time - start_total_time) / 1_000_000
    logging.info(f"REST: Total time: {time_ms:.4f} ms")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    benchmark("localhost:50051")
