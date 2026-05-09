from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.roadmap import Roadmap
from app.models.goal import Goal
from app.models.team_member import TeamMember

security = HTTPBearer()
jwt_manager = JWTManager()


async def update_goal_in_roadmap(
    roadmap_id: int,
    goal_title: str,
    goal_description: str | None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    
    try:
        sub = jwt_manager.verify_access_token(credentials.credentials)
        user_id = int(sub)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    
    roadmap_stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id)
    roadmap_result = await db.execute(roadmap_stmt)
    roadmap = roadmap_result.scalars().first()
    
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роудмап не найден"
        )
    
    # Проверяем доступ: создатель или член команды
    goal_stmt = select(Goal).where(Goal.goals_id == roadmap.goals_id)
    goal_result = await db.execute(goal_stmt)
    goal = goal_result.scalars().first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Цель не найдена"
        )
    
    # Может редактировать если создатель
    can_edit = goal.user_id == user_id
    
    # Или если роудмап в команде и он член команды
    if not can_edit and roadmap.team_id:
        team_member_stmt = select(TeamMember).where(
            TeamMember.team_id == roadmap.team_id,
            TeamMember.user_id == user_id
        )
        team_member_res = await db.execute(team_member_stmt)
        can_edit = team_member_res.scalars().first() is not None
    
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Цель не найдена или у вас нет разрешения на ее обновление"
        )
    
    goal.title = goal_title
    goal.description = goal_description
    
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    
    return {
        "status": "success",
        "message": "Goal updated successfully",
        "goal": {
            "goals_id": goal.goals_id,
            "title": goal.title,
            "description": goal.description
        }
    }
