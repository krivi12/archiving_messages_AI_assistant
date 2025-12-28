from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime
from uuid import UUID


class MessageCreate(BaseModel):
	message_id: UUID
	chat_id: UUID
	content: str
	rating: bool
	sent_at: datetime
	role: Literal["ai", "user"]


class MessageRead(MessageCreate):

	model_config = ConfigDict(from_attributes=True)

