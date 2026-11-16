from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version():
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json() == {"version": "1.0.0"}


def test_unknown_route_is_404():
    assert client.get("/does-not-exist").status_code == 404
