import logging
from concurrent import futures

import grpc

from gen import item_pb2
from gen import item_pb2_grpc

items_db: dict[int, item_pb2.Item] = {}
item_id_counter = 0


class ItemService(item_pb2_grpc.ItemServiceServicer):
    def GetItemList(
            self,
            request: item_pb2.GetItemListRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.GetItemListResponse:
        global items_db, item_id_counter

        logging.info("gRPC: GetItemList called")
        items = list(items_db.values())
        return item_pb2.GetItemListResponse(items=items)

    def GetItem(
            self,
            request: item_pb2.GetItemRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.Item:
        global items_db, item_id_counter

        logging.info(f"gRPC: GetItem called with id {request.id}")
        item = items_db.get(request.id)
        if item is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Item with id {request.id} not found")
            return item_pb2.Item()
        return item

    def AddItem(
            self,
            request: item_pb2.AddItemRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.Item:
        global items_db, item_id_counter

        logging.info(f"gRPC: AddItem called with name {request.name}")
        item_id_counter += 1
        item = item_pb2.Item(
            id=item_id_counter,
            name=request.name,
            value=request.value,
            details=request.details
        )
        items_db[item.id] = item
        return item

    def ClearItemList(
            self,
            request: item_pb2.ClearItemListRequest,
            context: grpc.ServicerContext,
    ) -> item_pb2.ClearItemListResponse:
        global items_db, item_id_counter

        logging.info("gRPC: ClearItemList called")
        items_db.clear()
        item_id_counter = 0
        return item_pb2.ClearItemListResponse()


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
