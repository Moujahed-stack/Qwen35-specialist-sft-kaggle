from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI()


class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


class Item(ItemIn):
    id: int


_items: dict[int, Item] = {}
_next_id = 1


@app.post("/items", response_model=Item, status_code=201)
def create_item(item: ItemIn):
    global _next_id
    new = Item(id=_next_id, **item.model_dump())
    _items[_next_id] = new
    _next_id += 1
    return new


@app.get("/items", response_model=list[Item])
def list_items():
    return list(_items.values())


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    return _items[item_id]


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    del _items[item_id]
    return Response(status_code=204)
