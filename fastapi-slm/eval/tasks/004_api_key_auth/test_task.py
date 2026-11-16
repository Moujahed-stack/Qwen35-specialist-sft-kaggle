from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
GOOD = {"X-API-Key": "secret-key"}


def test_public_needs_no_key():
    r = client.get("/public")
    assert r.status_code == 200
    assert r.json() == {"public": True}


def test_secure_with_valid_key():
    r = client.get("/secure", headers=GOOD)
    assert r.status_code == 200
    assert r.json() == {"secure": True}


def test_me_with_valid_key():
    r = client.get("/me", headers=GOOD)
    assert r.status_code == 200
    assert r.json() == {"user": "admin"}


def test_missing_key_is_401():
    assert client.get("/secure").status_code == 401
    assert client.get("/me").status_code == 401


def test_wrong_key_is_403():
    bad = {"X-API-Key": "nope"}
    assert client.get("/secure", headers=bad).status_code == 403
    assert client.get("/me", headers=bad).status_code == 403


def test_public_ignores_wrong_key():
    assert client.get("/public", headers={"X-API-Key": "nope"}).status_code == 200
