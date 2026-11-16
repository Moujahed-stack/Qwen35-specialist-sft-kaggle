from typing import Annotated, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[A-Za-z0-9]+$")
    age: int = Field(ge=13)
    nickname: Optional[str] = None


@app.get("/search")
def search(q: Annotated[str, Query(min_length=2)], limit: Annotated[int, Query(ge=1, le=50)] = 10):
    return {"q": q, "limit": limit}


@app.post("/users", status_code=201)
def create_user(user: UserIn):
    return user
