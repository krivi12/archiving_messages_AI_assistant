from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
import logging
import asyncio

from .database import engine, Base, AsyncSessionLocal
from . import models, schemas
from uuid import UUID

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.post("/messages", response_model=schemas.MessageRead, status_code=status.HTTP_201_CREATED, summary="Create a new message", description="Create a new message with the provided details.")
async def create_message(message_in: schemas.MessageCreate, db: AsyncSession = Depends(get_db)) -> schemas.MessageRead:
    """Create a new message in the database."""
    msg = models.Message(
        message_id=message_in.message_id,
        chat_id=message_in.chat_id,
        content=message_in.content,
        rating=message_in.rating,
        sent_at=message_in.sent_at,
        role=message_in.role,
    )
    db.add(msg)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Message already exists")
    except Exception as e:
        logging.error("Database error: %s", e)
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    await db.refresh(msg)
    return msg


@app.patch("/messages", response_model=schemas.MessageRead, status_code=status.HTTP_200_OK, summary="Update an existing message", description="Update the content of an existing message by its ID.")
async def update_message(message_id:UUID, message_content: str, db: AsyncSession = Depends(get_db)) -> schemas.MessageRead:
    """Update an existing message's content in the database."""

    result = await db.execute(select(models.Message).filter(models.Message.message_id == message_id))
    msg = result.scalars().first()

    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    else:
        msg.content = message_content
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        await db.refresh(msg)
        return msg


@app.get("/messages", response_model=list[schemas.MessageRead], status_code=status.HTTP_200_OK, summary="Retrieve messages with pagination", description="Get a paginated list of messages stored in the database.")    
async def read_messages(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> list[schemas.MessageRead]:
    """Retrieve all messages from the database."""
    result = await db.execute(select(models.Message).offset(skip).limit(limit))
    messages = result.scalars().all()
    return messages


@app.get("/messages/{message_id}", response_model=schemas.MessageRead, status_code=status.HTTP_200_OK, summary="Retrieve a single message", description="Get a specific message by its ID.")
async def read_message(message_id: UUID, db: AsyncSession = Depends(get_db)) -> schemas.MessageRead:
    """Retrieve a single message from the database."""
    result = await db.execute(select(models.Message).filter(models.Message.message_id == message_id))
    msg = result.scalars().first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return msg


@app.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a message", description="Delete a specific message by its ID.")
async def delete_message(message_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a message from the database."""
    result = await db.execute(select(models.Message).filter(models.Message.message_id == message_id))
    msg = result.scalars().first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    try:
        await db.delete(msg)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")


# uvicorn app.main:app --host 0.0.0.0 --port 8001
