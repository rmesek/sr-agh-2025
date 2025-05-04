from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class ItemBase(BaseModel):
    name: str
    value: float
    details: Optional[str] = None


class Item(ItemBase):
    id: int


items_db: dict[int, Item] = {}
item_id_counter = 0

app = FastAPI()


@app.get("/items", response_model=list[Item])
async def get_items():
    global items_db, item_id_counter

    return list(items_db.values())


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    global items_db, item_id_counter

    item = items_db.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")
    return item


@app.post("/items", response_model=Item, status_code=201)
async def add_item(item: ItemBase):
    global items_db, item_id_counter

    item_id_counter += 1
    item = Item(id=item_id_counter, **item.model_dump())
    items_db[item.id] = item
    return item


@app.delete("/items", status_code=204)
async def clear_items():
    global items_db, item_id_counter

    items_db.clear()
    item_id_counter = 0


def run(server_address: str):
    host, port = server_address.split(":")
    uvicorn.run(app, host=host, port=int(port))


if __name__ == "__main__":
    run("localhost:50051")
