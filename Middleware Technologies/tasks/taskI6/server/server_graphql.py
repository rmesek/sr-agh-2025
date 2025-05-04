from typing import Optional

import strawberry
import uvicorn
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.input
class ItemInput:
    name: str
    value: float
    details: Optional[str] = None


@strawberry.type
class Item:
    id: int
    name: str
    value: float
    details: Optional[str] = None


items_db: dict[int, Item] = {}
item_id_counter = 0

app = FastAPI()


@strawberry.type
class Query:
    @strawberry.field
    def items(self, ids: Optional[list[int]] = None) -> list[Item]:
        global items_db, item_id_counter

        if ids:
            return [item for item in items_db.values() if item.id in ids]
        return list(items_db.values())


@strawberry.type
class Mutation:
    @strawberry.mutation
    def items(self, items: list[ItemInput]) -> list[Item]:
        global items_db, item_id_counter

        added_items: list[Item] = []
        for item_input in items:
            item_id_counter += 1
            item = Item(
                id=item_id_counter,
                name=item_input.name,
                value=item_input.value,
                details=item_input.details
            )
            items_db[item.id] = item
            added_items.append(item)
        return added_items

    @strawberry.mutation
    def clear_items(self) -> None:
        global items_db, item_id_counter

        items_db.clear()
        item_id_counter = 0


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


def run(server_address: str):
    host, port = server_address.split(":")
    uvicorn.run(app, host=host, port=int(port))


if __name__ == "__main__":
    run("localhost:50051")
