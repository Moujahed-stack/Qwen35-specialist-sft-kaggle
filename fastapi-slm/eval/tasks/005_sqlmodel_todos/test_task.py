import os

if os.path.exists("todos.db"):
    os.remove("todos.db")

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_create_todo_defaults(client):
    r = client.post("/todos", json={"title": "buy milk"})
    assert r.status_code == 201
    body = r.json()
    assert isinstance(body["id"], int)
    assert body["title"] == "buy milk"
    assert body["done"] is False


def test_create_todo_done_true(client):
    r = client.post("/todos", json={"title": "already done", "done": True})
    assert r.status_code == 201
    assert r.json()["done"] is True


def test_uses_sqlite_file(client):
    client.post("/todos", json={"title": "persist me"})
    assert os.path.exists("todos.db")


def test_get_todo_and_404(client):
    created = client.post("/todos", json={"title": "read"}).json()
    r = client.get(f"/todos/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created
    assert client.get("/todos/99999").status_code == 404


def test_list_and_filter(client):
    open_t = client.post("/todos", json={"title": "open one", "done": False}).json()
    done_t = client.post("/todos", json={"title": "done one", "done": True}).json()

    all_ids = [t["id"] for t in client.get("/todos").json()]
    assert open_t["id"] in all_ids and done_t["id"] in all_ids

    done_list = client.get("/todos", params={"done": "true"}).json()
    assert all(t["done"] for t in done_list)
    assert done_t["id"] in [t["id"] for t in done_list]
    assert open_t["id"] not in [t["id"] for t in done_list]

    open_list = client.get("/todos", params={"done": "false"}).json()
    assert all(not t["done"] for t in open_list)
    assert open_t["id"] in [t["id"] for t in open_list]
    assert done_t["id"] not in [t["id"] for t in open_list]


def test_patch_updates_only_done(client):
    created = client.post("/todos", json={"title": "patch me"}).json()
    r = client.patch(f"/todos/{created['id']}", json={"done": True})
    assert r.status_code == 200
    assert r.json() == {"id": created["id"], "title": "patch me", "done": True}
    assert client.get(f"/todos/{created['id']}").json()["done"] is True
    assert client.patch("/todos/99999", json={"done": True}).status_code == 404


def test_delete(client):
    created = client.post("/todos", json={"title": "remove"}).json()
    assert client.delete(f"/todos/{created['id']}").status_code == 204
    assert client.get(f"/todos/{created['id']}").status_code == 404
    assert client.delete("/todos/99999").status_code == 404


def test_title_validation_422(client):
    assert client.post("/todos", json={"done": True}).status_code == 422
    assert client.post("/todos", json={"title": ""}).status_code == 422
