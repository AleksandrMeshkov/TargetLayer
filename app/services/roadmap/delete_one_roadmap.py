from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database.database import get_db
from app.core.security.jwt import JWTManager
from app.models.user import User
from app.models.roadmap import Roadmap
from app.models.goal import Goal

security = HTTPBearer()
jwt_manager = JWTManager()


async def delete_user_roadmap(
    roadmap_id: int,
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
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )
    
    # Get roadmap and verify user ownership through goal
    roadmap_stmt = select(Roadmap).where(Roadmap.roadmap_id == roadmap_id)
    roadmap_result = await db.execute(roadmap_stmt)
    roadmap = roadmap_result.scalars().first()
    
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found"
        )
    
    # Verify user owns the goal associated with this roadmap
    goal_stmt = select(Goal).where(
        (Goal.goals_id == roadmap.goals_id) &
        (Goal.user_id == user_id)
    )
    goal_result = await db.execute(goal_stmt)
    goal = goal_result.scalars().first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found or you don't have permission to delete it"
        )
    
    # Delete roadmap (tasks will cascade delete)
    db.delete(roadmap)
    await db.commit()
    
    return {
        "status": "success",
        "message": "Roadmap deleted successfully",
        "roadmap_id": roadmap_id
    }
