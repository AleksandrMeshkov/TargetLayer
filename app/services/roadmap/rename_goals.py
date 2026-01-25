from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.user_roadmap import UserRoadmap
from app.models.roadmap import Roadmap
from app.models.goal import Goal

security = HTTPBearer()
jwt_manager = JWTManager()


async def update_goal_in_roadmap(
    roadmap_id: int,
    goal_title: str,
    goal_description: str | None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    
    token = credentials.credentials
    payload = jwt_manager.decode_token(token)
    
    if isinstance(payload, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=payload
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    try:
        user_activity_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )
    
    stmt = select(UserRoadmap).where(
        (UserRoadmap.user_activity_id == user_activity_id) &
        (UserRoadmap.roadmap_id == roadmap_id)
    )
    result = await db.execute(stmt)
    user_roadmap = result.scalars().first()
    
    if not user_roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found or you don't have permission to update it"
        )
    
    roadmap_stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id)
    roadmap_result = await db.execute(roadmap_stmt)
    roadmap = roadmap_result.scalars().first()
    
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found"
        )
    
    goal_stmt = select(Goal).where(Goal.goals_id == roadmap.goals_id)
    goal_result = await db.execute(goal_stmt)
    goal = goal_result.scalars().first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
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
