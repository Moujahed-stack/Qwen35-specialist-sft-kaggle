from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_search_defaults():
    r = client.get("/search", params={"q": "abc"})
    assert r.status_code == 200
    assert r.json() == {"q": "abc", "limit": 10}


def test_search_limit_bounds():
    assert client.get("/search", params={"q": "ab", "limit": 1}).json() == {"q": "ab", "limit": 1}
    assert client.get("/search", params={"q": "ab", "limit": 50}).json() == {"q": "ab", "limit": 50}
    assert client.get("/search", params={"q": "ab", "limit": 0}).status_code == 422
    assert client.get("/search", params={"q": "ab", "limit": 51}).status_code == 422
    assert client.get("/search", params={"q": "ab", "limit": "abc"}).status_code == 422


def test_search_q_rules():
    assert client.get("/search", params={"q": "a"}).status_code == 422
    assert client.get("/search").status_code == 422


def test_create_user_ok_without_nickname():
    r = client.post("/users", json={"username": "alice1", "age": 30})
    assert r.status_code == 201
    assert r.json() == {"username": "alice1", "age": 30, "nickname": None}


def test_create_user_with_nickname():
    r = client.post("/users", json={"username": "bob", "age": 13, "nickname": "bobby"})
    assert r.status_code == 201
    assert r.json() == {"username": "bob", "age": 13, "nickname": "bobby"}


def test_username_rules():
    ok = {"age": 20}
    assert client.post("/users", json={**ok, "username": "ab"}).status_code == 422
    assert client.post("/users", json={**ok, "username": "a" * 21}).status_code == 422
    assert client.post("/users", json={**ok, "username": "a" * 20}).status_code == 201
    assert client.post("/users", json={**ok, "username": "bad name!"}).status_code == 422
    assert client.post("/users", json={**ok, "username": "user_1"}).status_code == 422


def test_age_rules():
    assert client.post("/users", json={"username": "carol", "age": 12}).status_code == 422
    assert client.post("/users", json={"username": "carol", "age": "x"}).status_code == 422
    assert client.post("/users", json={"username": "carol"}).status_code == 422
