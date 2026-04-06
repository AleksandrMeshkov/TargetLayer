from app.services.team_service.out_user_team import leave_team as leave_team_service
from fastapi import APIRouter, Depends, Path, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas import team as team_schemas
from app.services.team_service.create_team import create_team as create_team_service
from app.services.team_service.delete_team import delete_team as delete_team_service
from app.services.team_service.get_team_members import get_team_members
from app.services.team_service.get_user_teams import get_user_teams
from app.services.team_service.send_team_invite_email import send_team_invite_email
from app.services.team_service.rename_team import rename_team as rename_team_service
from app.services.team_service.update_member_role import update_team_member_role
from app.services.user.get_my_user import get_current_user
from app.core.settings.settings import settings
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get(
	"/invite/accept",
	status_code=status.HTTP_302_FOUND,
)
async def accept_invite_link_redirect(token: str):
	frontend_url = settings.build_frontend_team_invite_url(token)
	return RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)


@router.post(
	"/{team_id}/invite-email",
	response_model=team_schemas.TeamInviteEmailResponse,
	status_code=status.HTTP_200_OK,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def invite_user_by_email(
	team_id: int = Path(..., gt=0),
	payload: team_schemas.TeamInviteEmailRequest = ..., 
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> team_schemas.TeamInviteEmailResponse:
	result = await send_team_invite_email(
		db=db,
		current_user=current_user,
		team_id=team_id,
		invited_user_id=payload.user_id,
	)
	return team_schemas.TeamInviteEmailResponse(**result)


@router.get(
	"/my-teams",
	response_model=team_schemas.TeamListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_my_teams(
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> team_schemas.TeamListResponse:
	teams = await get_user_teams(db, current_user)
	return team_schemas.TeamListResponse(teams=teams, total=len(teams))


@router.get(
	"/{team_id}/users",
	response_model=team_schemas.TeamMemberListResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def get_team_users(
	team_id: int = Path(..., gt=0),
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> team_schemas.TeamMemberListResponse:
	members = await get_team_members(db, current_user, team_id)
	return team_schemas.TeamMemberListResponse(users=members, total=len(members))


@router.post(
	"",
	response_model=team_schemas.TeamResponse,
	status_code=status.HTTP_201_CREATED,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def create_team(
	payload: team_schemas.TeamCreateRequest,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Team:
	return await create_team_service(db, current_user, payload.name)

@router.put(
	"/{team_id}",
	response_model=team_schemas.TeamResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def rename_team(
	team_id: int = Path(..., gt=0),
	payload: team_schemas.TeamUpdateRequest = ...,
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
	response_model=team_schemas.TeamMemberResponse,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def update_member_role(
	team_id: int = Path(..., gt=0),
	user_id: int = Path(..., gt=0),
	payload: team_schemas.TeamMemberRoleUpdateRequest = ...,
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
