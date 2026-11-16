from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_first_item_gets_id_1():
    r = client.post("/items", json={"name": "pen", "price": 1.5})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "name": "pen", "price": 1.5}


def test_ids_increment():
    a = client.post("/items", json={"name": "a", "price": 1}).json()["id"]
    b = client.post("/items", json={"name": "b", "price": 2}).json()["id"]
    assert b == a + 1


def test_get_item():
    created = client.post("/items", json={"name": "cup", "price": 3.25}).json()
    r = client.get(f"/items/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_missing_item_404():
    assert client.get("/items/99999").status_code == 404


def test_list_contains_created_items_in_order():
    a = client.post("/items", json={"name": "first", "price": 1}).json()
    b = client.post("/items", json={"name": "second", "price": 2}).json()
    r = client.get("/items")
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert a["id"] in ids and b["id"] in ids
    assert ids.index(a["id"]) < ids.index(b["id"])
    assert ids == sorted(ids)


def test_delete_item():
    created = client.post("/items", json={"name": "tmp", "price": 5}).json()
    r = client.delete(f"/items/{created['id']}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/items/{created['id']}").status_code == 404


def test_delete_missing_404():
    assert client.delete("/items/99999").status_code == 404


def test_invalid_bodies_422():
    assert client.post("/items", json={"name": "x", "price": 0}).status_code == 422
    assert client.post("/items", json={"name": "x", "price": -3}).status_code == 422
    assert client.post("/items", json={"price": 3}).status_code == 422
    assert client.post("/items", json={"name": "", "price": 3}).status_code == 422
    assert client.post("/items", json={"name": "x", "price": "abc"}).status_code == 422
