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

        ######### clear items #########
        try:
            s.delete(f"{base_url}/items")
        except requests.RequestException as e:
            logging.error(f"REST: ClearItems failed with error: {e}")
            return
        ###############################

        ########## add items ##########
        new_items = [
            {"name": f"Item {i}", "value": 10.0 * i, "details": f"Details for item {i}"}
            for i in range(item_number)
        ]
        try:
            start_time = time.perf_counter_ns()
            for add_request in new_items:
                s.post(f"{base_url}/items", json=add_request)
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"REST: AddItem failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"REST: Added items ({len(new_items)}) in {time_ms:.4f} ms")
        add_requests_size = sum(len(str(add_request).encode("utf-8")) for add_request in new_items)
        logging.info(f"REST: Sum of add_requests size: {add_requests_size} bytes")
        ###############################

        ########## get items ##########
        try:
            start_time = time.perf_counter_ns()
            get_response = s.get(f"{base_url}/items")
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"REST: GetItems failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"REST: Retrieved items ({len(get_response.json())}) in {time_ms:.4f} ms")
        get_response_size = len(get_response.content)
        logging.info(f"REST: get_response size: {get_response_size} bytes")
        ###############################

    stop_total_time = time.perf_counter_ns()
    time_ms = (stop_total_time - start_total_time) / 1_000_000
    logging.info(f"REST: Total time: {time_ms:.4f} ms")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    benchmark("localhost:50051")
