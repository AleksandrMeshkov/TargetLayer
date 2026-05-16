from app.services.team_service.out_user_team import leave_team as leave_team_service
from fastapi import APIRouter, Depends, Path, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas import team as team_schemas
from app.services.team_service.accept_team_invite import accept_team_invite
from app.services.team_service.create_team import create_team as create_team_service
from app.services.team_service.delete_team import delete_team as delete_team_service
from app.services.team_service.get_team_members import get_team_members
from app.services.team_service.get_user_teams import get_user_teams
from app.services.team_service.send_team_invite_email import send_team_invite_email
from app.services.team_service.rename_team import rename_team as rename_team_service
from app.services.team_service.update_member_role import update_team_member_role
from app.services.user.get_my_user import get_current_user
from app.core.settings.settings import settings
from fastapi.responses import HTMLResponse


router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get(
	"/invite/accept",
	response_class=HTMLResponse,
	status_code=status.HTTP_200_OK,
)
async def accept_invite_link_redirect(token: str):
	frontend_base = (settings.FRONTEND_URL or settings.server_base_url).rstrip("/")
	login_url = f"{frontend_base}/login"
	html = f"""
<!doctype html>
<html lang=\"ru\">
<head>
	<meta charset=\"utf-8\" />
	<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
	<title>Принятие приглашения</title>
	<style>
		body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
		.wrap {{ min-height: 100vh; display: grid; place-items: center; padding: 24px; }}
		.card {{ width: 100%; max-width: 560px; background: #111827; border: 1px solid #334155; border-radius: 14px; padding: 20px; }}
		h1 {{ margin: 0 0 12px; font-size: 24px; }}
		p {{ margin: 0 0 12px; line-height: 1.5; color: #cbd5e1; }}
		.status {{ margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: #1f2937; color: #e5e7eb; }}
		.ok {{ background: #064e3b; color: #d1fae5; }}
		.err {{ background: #7f1d1d; color: #fee2e2; }}
		.btn {{ display: inline-block; margin-top: 12px; background: #2563eb; color: #fff; text-decoration: none; padding: 10px 14px; border-radius: 10px; }}
		.muted {{ font-size: 13px; color: #94a3b8; }}
	</style>
</head>
<body>
	<div class=\"wrap\">
		<div class=\"card\">
			<h1>Приглашение в команду</h1>
			<p id=\"msg\">Проверяем приглашение и пытаемся принять его автоматически...</p>
			<div id=\"status\" class=\"status\">Подготовка...</div>
			<a id=\"loginBtn\" class=\"btn\" href=\"{login_url}\" style=\"display:none\">Войти</a>
			<p class=\"muted\">Если вы не авторизованы, войдите и снова откройте ссылку из письма.</p>
		</div>
	</div>

	<script>
		(async () => {{
			const params = new URLSearchParams(window.location.search);
			const inviteToken = params.get('token');
			const statusEl = document.getElementById('status');
			const msgEl = document.getElementById('msg');
			const loginBtn = document.getElementById('loginBtn');

			if (!inviteToken) {{
				statusEl.className = 'status err';
				statusEl.textContent = 'Токен приглашения отсутствует.';
				msgEl.textContent = 'Ссылка приглашения некорректна.';
				return;
			}}

			const accessToken = localStorage.getItem('tl_access_token');
			if (!accessToken) {{
				statusEl.className = 'status err';
				statusEl.textContent = 'Вы не авторизованы.';
				msgEl.textContent = 'Войдите в аккаунт и снова откройте эту ссылку.';
				loginBtn.style.display = 'inline-block';
				return;
			}}

			try {{
				const resp = await fetch('/api/v1/teams/invite/accept', {{
					method: 'POST',
					headers: {{
						'Content-Type': 'application/json',
						'Authorization': `Bearer ${{accessToken}}`,
					}},
					credentials: 'include',
					body: JSON.stringify({{ token: inviteToken }}),
				}});

				const data = await resp.json().catch(() => ({{}}));
				if (!resp.ok) {{
					const detail = data && data.detail ? data.detail : 'Не удалось принять приглашение.';
					statusEl.className = 'status err';
					statusEl.textContent = detail;
					if (resp.status === 401) {{
						msgEl.textContent = 'Сессия истекла. Войдите и попробуйте снова.';
						loginBtn.style.display = 'inline-block';
					}}
					return;
				}}

				statusEl.className = 'status ok';
				statusEl.textContent = 'Приглашение успешно принято.';
				msgEl.textContent = 'Перенаправляем в раздел команд...';
				setTimeout(() => {{
					window.location.href = '/app/teams';
				}}, 900);
			}} catch (e) {{
				statusEl.className = 'status err';
				statusEl.textContent = 'Ошибка сети при принятии приглашения.';
			}}
		}})();
	</script>
</body>
</html>
"""
	return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


@router.post(
	"/invite/accept",
	response_model=team_schemas.TeamInviteAcceptResponse,
	status_code=status.HTTP_200_OK,
	openapi_extra={"security": [{"Bearer": []}]},
)
async def accept_invite_link(
	payload: team_schemas.TeamInviteAcceptRequest,
	current_user: User = Security(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> team_schemas.TeamInviteAcceptResponse:
	result = await accept_team_invite(
		db=db,
		current_user=current_user,
		token=payload.token,
	)
	return team_schemas.TeamInviteAcceptResponse(**result)


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
		payload.role_id,
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
