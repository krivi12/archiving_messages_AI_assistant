from fastapi.testclient import TestClient
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app.database as db_test
import app.main as main

engine = db_test.engine
SessionLocal = db_test.SessionLocal
client = TestClient(main.app)


@pytest.fixture(scope="session", autouse=True)
def manage_schema():
    """Create tables for the test session and drop them afterward.

    This makes tests exercise the real DB configuration while ensuring data
    and schema are removed after the run.
    """
    db_test.Base.metadata.create_all(bind=engine)
    yield
    db_test.Base.metadata.drop_all(bind=engine)


def make_payload(id_str="11111111-1111-1111-1111-111111111119"):
    return {
        "message_id": id_str,
        "chat_id": "22222222-2222-2222-2222-222222222222",
        "content": "hello",
        "rating": False,
        "sent_at": "2025-12-29T12:00:00Z",
        "role": "user",
    }


def test_create_message():
    payload = make_payload()
    r = client.post("/messages", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["message_id"] == payload["message_id"]
    assert data["content"] == payload["content"]


def test_create_duplicate_message():
    payload = make_payload()
    r = client.post("/messages", json=payload)
    assert r.status_code == 409


def test_notexist_update_message():
    payload = make_payload("11111111-1111-1111-1111-111111111114")
    r = client.patch(
        "/messages",
        params={"message_id": payload["message_id"], "message_content": "content114"},
    )
    assert r.status_code == 404


def test_update_message():
    payload = make_payload("11111111-1111-1111-1111-111111111114")
    r = client.post("/messages", json=payload)
    assert r.status_code == 201
    
    r = client.patch(
        "/messages",
        params={"message_id": payload["message_id"], "message_content": "updated content"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["content"] == "updated content"


def test_read_messages():
    payload = make_payload("11111111-1111-1111-1111-111111111115")
    client.post("/messages", json=payload)

    r = client.get("/messages/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
