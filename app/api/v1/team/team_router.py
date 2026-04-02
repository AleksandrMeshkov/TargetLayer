from app.services.team_service.out_user_team import leave_team as leave_team_service
from datetime import datetime
from fastapi import APIRouter, Depends, Path, Security, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.team_service.create_team import create_team as create_team_service
from app.services.team_service.delete_team import delete_team as delete_team_service
from app.services.team_service.get_team_members import get_team_members
from app.services.team_service.get_user_teams import get_user_teams
from app.services.team_service.invite_team_create import accept_team_invite, create_team_invite_link
from app.services.team_service.rename_team import rename_team as rename_team_service
from app.services.team_service.update_member_role import update_team_member_role
from app.services.user.get_my_user import get_current_user


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


router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.post(
	"/{team_id}/invite-links",
	response_model=TeamInviteCreateResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def create_invite_link(
	team_id: int = Path(..., gt=0),
	payload: TeamInviteCreateRequest = ...,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> TeamInviteCreateResponse:
	invite = await create_team_invite_link(
		db,
		current_user,
		team_id,
		uses_left=payload.uses_left,
	)
	return TeamInviteCreateResponse(**invite)


@router.post(
	"/invite/accept",
	response_model=TeamInviteAcceptResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def accept_invite_link(
	payload: TeamInviteAcceptRequest,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> TeamInviteAcceptResponse:
	result = await accept_team_invite(db, current_user, payload.token)
	return TeamInviteAcceptResponse(**result)


@router.get(
	"/my-teams",
	response_model=TeamListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_my_teams(
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> TeamListResponse:
	teams = await get_user_teams(db, current_user)
	return TeamListResponse(teams=teams, total=len(teams))


@router.get(
	"/{team_id}/users",
	response_model=TeamMemberListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_team_users(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> TeamMemberListResponse:
	members = await get_team_members(db, current_user, team_id)
	return TeamMemberListResponse(users=members, total=len(members))


@router.post(
	"",
	response_model=TeamResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def create_team(
	payload: TeamCreateRequest,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Team:
	return await create_team_service(db, current_user, payload.name)

@router.put(
	"/{team_id}",
	response_model=TeamResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def rename_team(
	team_id: int = Path(..., gt=0),
	payload: TeamUpdateRequest = ...,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Team:
	return await rename_team_service(db, current_user, team_id, payload.name)

@router.delete(
	"/{team_id}/leave",
	response_model=dict,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def leave_team(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	await leave_team_service(db, current_user, team_id)
	return {"status": "success", "message": "You have left the team"}


@router.patch(
	"/{team_id}/users/{user_id}/role",
	response_model=TeamMemberResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def update_member_role(
	team_id: int = Path(..., gt=0),
	user_id: int = Path(..., gt=0),
	payload: TeamMemberRoleUpdateRequest = ...,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> TeamMember:
	member = await update_team_member_role(
		db,
		current_user,
		team_id,
		user_id,
		payload.role,
	)
	return member

@router.delete(
	"/{team_id}",
	response_model=dict,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def delete_team(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	await delete_team_service(db, current_user, team_id)
	return {"status": "success", "message": "Team deleted"}
