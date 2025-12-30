# archiving_messages_AI_assistant

Lightweight FastAPI service for archiving chat messages to PostgreSQL.

## Quick start

Required environment variables (`.env`):
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`


### Start production database and app
```bash
docker compose -f docker-compose.prod.yml -p prod up --build
```

### Run locally (VS Code devcontainer workflow):

1. Open the project in VS Code and start the devcontainer. The `api` service may default to `sleep infinity` so the app won't be running automatically.

2. By default the api container sleeps (sleep infinity)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API overview

Main files:
- `app/main.py` — FastAPI routes and DB lifecycle.
- `app/database.py` — SQLAlchemy engine, `SessionLocal`, and `Base`.
- `app/models.py` — `Message` model (UUID PK `message_id`).
- `app/schemas.py` — Pydantic request/response schemas.

- Endpoints (examples):

  - POST `/messages` — create a message (returns 201)

    Example body:

    ```json
    {
      "message_id": "11111111-1111-1111-1111-111111111111",
      "chat_id": "22222222-2222-2222-2222-222222222222",
      "content": "hello",
      "rating": false,
      "sent_at": "2025-12-28T12:00:00Z",
      "role": "user"
    }
    ```

    Examples

    - POST `/messages` — create a message (returns 201)

      ```bash
      curl -X POST http://localhost:8000/messages \
        -H "Content-Type: application/json" \
        -d '{"message_id":"11111111-1111-1111-1111-111111111111","chat_id":"22222222-2222-2222-2222-222222222222","content":"hello","rating":false,"sent_at":"2025-12-28T12:00:00Z","role":"user"}'
      ```

    - PATCH `/messages` — update message content by `message_id` (query params)

      ```bash
      curl -X PATCH "http://localhost:8000/messages?message_id=11111111-1111-1111-1111-111111111111&message_content=updated%20hello"
      ```

    - GET `/messages/` — list all messages

      ```bash
      curl http://localhost:8000/messages/
      ```

    - GET `/messages/{message_id}` — get a single message

      ```bash
      curl http://localhost:8000/messages/11111111-1111-1111-1111-111111111111
      ```

    - DELETE `/messages/{message_id}` — delete a message

      ```bash
      curl -X DELETE http://localhost:8000/messages/11111111-1111-1111-1111-111111111111
      ```

    Note: the examples use port `8000` (production); when running the dev container the service is served on port `8001`.


### Check messages
- prod:
  ```bash
  docker exec -it <container> bash
  psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-prod_db}
  SELECT * FROM messages;
  ```
- dev:
  ```bash
  psql -h db -p 5432 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-devdb}" -c "SELECT * FROM messages;"
  ```

### Testing

Run the endpoint tests in a devcontainer (tests create the DB schema at test start and drop it after the run):

1. Ensure environment variables are available inside the devcontainer (or set them in `.env`).

2. Run the tests (from the project root inside the devcontainer):

```bash
PYTHONPATH=. pytest -q tests/test_endpoints.py
```
