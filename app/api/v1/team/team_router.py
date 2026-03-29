from datetime import datetime

from fastapi import APIRouter, Depends, Path, Security, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.team_service.team_service import TeamService
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


router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get(
	"/my-teams",
	response_model=TeamListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_my_teams(
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> TeamListResponse:
	service = TeamService(db)
	teams = await service.get_user_teams(current_user)
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
	service = TeamService(db)
	members = await service.get_team_members(current_user, team_id)
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
	service = TeamService(db)
	return await service.create_team(current_user, payload.name)


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
	service = TeamService(db)
	await service.delete_team(current_user, team_id)
	return {"status": "success", "message": "Team deleted"}


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
	service = TeamService(db)
	return await service.rename_team(current_user, team_id, payload.name)
