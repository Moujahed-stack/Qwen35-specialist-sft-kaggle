from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

engine = create_engine("sqlite:///todos.db", connect_args={"check_same_thread": False})


class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False


class TodoCreate(SQLModel):
    title: str = Field(min_length=1)
    done: bool = False


class TodoUpdate(BaseModel):
    done: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


def get_session():
    with Session(engine) as session:
        yield session


@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(data: TodoCreate, session: Session = Depends(get_session)):
    todo = Todo.model_validate(data)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.get("/todos", response_model=list[Todo])
def list_todos(done: Optional[bool] = None, session: Session = Depends(get_session)):
    stmt = select(Todo)
    if done is not None:
        stmt = stmt.where(Todo.done == done)
    return session.exec(stmt).all()


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, data: TodoUpdate, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.done = data.done
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
    return Response(status_code=204)
