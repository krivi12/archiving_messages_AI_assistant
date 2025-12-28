from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
import logging
# from sqlalchemy import UUID4

from .database import engine, Base, SessionLocal
from . import models, schemas

@asynccontextmanager
async def lifespan(app):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logging.getLogger(__name__).warning("Could not create tables at startup: %s", exc)
    yield

app = FastAPI(lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/messages", response_model=schemas.MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(message_in: schemas.MessageCreate, db: Session = Depends(get_db)) -> schemas.MessageRead:
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
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Message already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    db.refresh(msg)
    return msg


@app.patch("/messages", response_model=schemas.MessageRead, status_code=status.HTTP_200_OK)
async def update_message(message_id, message_content: str, db: Session = Depends(get_db)) -> schemas.MessageRead:

    msg = db.query(models.Message).filter(models.Message.message_id == message_id).first()

    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    else:
        msg.content = message_content
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        db.refresh(msg)
        return msg

@app.get("/messages/", status_code=status.HTTP_200_OK)    
async def read_messages(db: Session = Depends(get_db)) -> list[schemas.MessageRead]:
    messages = db.query(models.Message).all()
    print(type(messages[0]))
    return messages


# uvicorn app.main:app --host 0.0.0.0 --port 8001
