from fastapi.testclient import TestClient
import sys
import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app.main as main
from app.database import Base
import uuid
import sqlite3

sqlite3.register_adapter(uuid.UUID, lambda u: u.hex)

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)

async def override_get_db():
    async with sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        try:
            yield session
        finally:
            await session.close()

main.app.dependency_overrides[main.get_db] = override_get_db

client = TestClient(main.app)


@pytest.fixture(scope="session", autouse=True)
def manage_schema():
    """Create tables for the test session and drop them afterward.

    This makes tests exercise the real DB configuration while ensuring data
    and schema are removed after the run.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_create())
    yield
    loop.run_until_complete(async_drop())
    loop.close()


async def async_create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def async_drop():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def make_payload(id_str="a1111111-1111-1111-1111-111111111119"):
    return {
        "message_id": id_str,
        "chat_id": "b2222222-2222-2222-2222-222222222222",
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
    payload = make_payload("a1111111-1111-1111-1111-111111111114")
    r = client.patch(
        "/messages",
        params={"message_id": payload["message_id"], "message_content": "content114"},
    )
    assert r.status_code == 404


def test_update_message():
    payload = make_payload("a1111111-1111-1111-1111-111111111114")
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
    payload = make_payload("a1111111-1111-1111-1111-111111111115")
    client.post("/messages", json=payload)

    r = client.get("/messages/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_read_single_message():
    payload = make_payload("a1111111-1111-1111-1111-111111111116")
    client.post("/messages", json=payload)

    r = client.get(f"/messages/{payload['message_id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["message_id"] == payload["message_id"]
    assert data["content"] == payload["content"]


def test_read_single_message_not_found():
    r = client.get("/messages/a1111111-1111-1111-1111-111111111117")
    assert r.status_code == 404


def test_delete_message():
    payload = make_payload("a1111111-1111-1111-1111-111111111118")
    client.post("/messages", json=payload)

    r = client.delete(f"/messages/{payload['message_id']}")
    assert r.status_code == 204

    r = client.get(f"/messages/{payload['message_id']}")
    assert r.status_code == 404


def test_delete_message_not_found():
    r = client.delete("/messages/99999999-9999-9999-9999-999999999999")
    assert r.status_code == 404

