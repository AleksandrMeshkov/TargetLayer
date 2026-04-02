from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TeamCreateRequest(BaseModel):
	name: str = Field(min_length=1, max_length=255)


class TeamUpdateRequest(BaseModel):
	name: str = Field(min_length=1, max_length=255)


class TeamResponse(BaseModel):
	team_id: int
	name: str
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class TeamListResponse(BaseModel):
	teams: list[TeamResponse]
	total: int

	model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
	id: int
	team_id: int
	user_id: int
	team_role_id: int
	joined_at: datetime

	model_config = ConfigDict(from_attributes=True)


class TeamMemberListResponse(BaseModel):
	users: list[TeamMemberResponse]
	total: int

	model_config = ConfigDict(from_attributes=True)


class TeamInviteCreateRequest(BaseModel):
	uses_left: int = Field(default=1, ge=1, le=100)


class TeamInviteCreateResponse(BaseModel):
	token: str
	team_id: int
	permission: str
	uses_left: int | None
	expires_at: datetime


class TeamInviteAcceptRequest(BaseModel):
	token: str = Field(min_length=1)


class TeamInviteAcceptResponse(BaseModel):
	team_id: int
	user_id: int
	team_role_id: int
	joined_at: datetime
	status: str


class TeamMemberRoleUpdateRequest(BaseModel):
	role: str = Field(min_length=1, max_length=50)
