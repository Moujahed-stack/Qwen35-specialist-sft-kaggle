from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class SumRequest(BaseModel):
    numbers: list[float] = Field(default_factory=list)


@app.get("/api/greet")
def greet(name: str = "World"):
    return {"greeting": f"Hello, {name}!"}


@app.post("/api/sum")
def total(data: SumRequest):
    return {"sum": sum(data.numbers)}


@app.get("/api/echo/{item_id}")
def echo(item_id: int):
    return {"id": item_id}
