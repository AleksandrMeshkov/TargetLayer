from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatCreateRequest(BaseModel):
    team_id: int = Field(gt=0)
    participant_user_ids: list[int] = Field(default_factory=list)
    name: str | None = Field(default=None, max_length=255)


class ChatResponse(BaseModel):
    chat_id: int
    team_id: int
    type: str
    name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    type: str = Field(default="text", max_length=50)


class MessageResponse(BaseModel):
    message_id: int
    chat_id: int
    user_id: int
    type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessagesListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


class ChatListResponse(BaseModel):
    chats: list[ChatResponse]
    total: int


class ChatParticipantResponse(BaseModel):
    id: int
    chat_id: int
    user_id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatParticipantsListResponse(BaseModel):
    participants: list[ChatParticipantResponse]
    total: int
