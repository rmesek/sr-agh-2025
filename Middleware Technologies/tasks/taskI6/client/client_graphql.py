import logging
import time

import requests

CLEAR_ITEMS_MUTATION = r"""
mutation ClearItems {
  clearItems
}
"""

ADD_ITEMS_MUTATION = r"""
mutation AddItems($items: [ItemInput!]!) {
  items(items: $items) {
    id
    name
    value
    details
  }
}
"""

GET_ITEMS_QUERY = r"""
query GetItems($ids: [Int!]) {
  items(ids: $ids) {
    id
    name
    value
    details
  }
}
"""


def benchmark(server_address: str, item_number: int = 1000):
    base_url = f"http://{server_address}"
    logging.info(f"GraphQL: benchmark {server_address}")

    start_total_time = time.perf_counter_ns()
    with requests.Session() as s:
        stop_time = time.perf_counter_ns()
        time_ms = (stop_time - start_total_time) / 1_000_000
        logging.info(f"GraphQL: Session created in {time_ms:.4f} ms")

        ######### clear items #########
        try:
            s.post(f"{base_url}/graphql", json={"query": CLEAR_ITEMS_MUTATION})
        except requests.RequestException as e:
            logging.error(f"GraphQL: ClearItems failed with error: {e}")
            return
        ###############################

        ########## add items ##########
        new_items = [
            {"name": f"Item {i}", "value": 10.0 * i, "details": f"Details for item {i}"}
            for i in range(item_number)
        ]
        add_request = {
            "query": ADD_ITEMS_MUTATION,
            "variables": {"items": new_items}
        }
        try:
            start_time = time.perf_counter_ns()
            s.post(f"{base_url}/graphql", json=add_request)
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"GraphQL: AddItems failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(f"GraphQL: Added items ({len(add_request["variables"]["items"])}) in {time_ms:.4f} ms")
        add_request_size = len(str(add_request).encode("utf-8"))
        logging.info(f"GraphQL: add_request size: {add_request_size} bytes")
        ###############################

        ########## get items ##########
        try:
            start_time = time.perf_counter_ns()
            get_response = s.post(f"{base_url}/graphql", json={"query": GET_ITEMS_QUERY})
            stop_time = time.perf_counter_ns()
        except requests.RequestException as e:
            logging.error(f"GraphQL: GetItems failed with error: {e}")
            return
        time_ms = (stop_time - start_time) / 1_000_000
        logging.info(
            f"GraphQL: Retrieved items ({len(get_response.json()["data"]["items"])}) in {time_ms:.4f} ms")
        get_response_size = len(get_response.content)
        logging.info(f"GraphQL: get_response size: {get_response_size} bytes")
        ###############################

    stop_total_time = time.perf_counter_ns()
    time_ms = (stop_total_time - start_total_time) / 1_000_000
    logging.info(f"GraphQL: Total time: {time_ms:.4f} ms")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    benchmark("localhost:50051")
