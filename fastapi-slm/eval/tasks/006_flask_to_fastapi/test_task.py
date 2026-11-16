from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_greet_default():
    r = client.get("/api/greet")
    assert r.status_code == 200
    assert r.json() == {"greeting": "Hello, World!"}


def test_greet_with_name():
    assert client.get("/api/greet", params={"name": "Sam"}).json() == {"greeting": "Hello, Sam!"}


def test_sum():
    r = client.post("/api/sum", json={"numbers": [1, 2, 3.5]})
    assert r.status_code == 200
    assert r.json()["sum"] == 6.5


def test_sum_defaults_to_empty_list():
    r = client.post("/api/sum", json={})
    assert r.status_code == 200
    assert r.json()["sum"] == 0


def test_sum_invalid_body_422():
    assert client.post("/api/sum", json={"numbers": "nope"}).status_code == 422
    assert client.post("/api/sum", json={"numbers": [1, "x"]}).status_code == 422


def test_echo():
    r = client.get("/api/echo/7")
    assert r.status_code == 200
    assert r.json() == {"id": 7}


def test_echo_non_integer_422():
    assert client.get("/api/echo/abc").status_code == 422


def test_uses_fastapi_not_flask():
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)
