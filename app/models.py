from sqlalchemy import Column, String, UUID, DateTime, Boolean
from .database import Base

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    chat_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    content = Column(String, nullable=False)
    rating = Column(Boolean, nullable=False)
    sent_at = Column(DateTime, nullable=False)
    role = Column(String, nullable=False)

