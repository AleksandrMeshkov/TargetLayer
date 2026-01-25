from fastapi import APIRouter, Depends, HTTPException, status, Security, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.schemas.roadmap import RoadmapResponse, RoadmapsListResponse
from app.services.roadmap.get_all_roadmap import get_user_roadmaps
from app.services.roadmap.delete_one_roadmap import delete_user_roadmap
from app.models.roadmap import Roadmap

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])
security = HTTPBearer()


@router.get(
    "/my-roadmaps",
    response_model=RoadmapsListResponse,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def get_my_roadmaps(
    credentials: HTTPAuthorizationCredentials = Security(security),
    roadmaps: list[Roadmap] = Depends(get_user_roadmaps)
):
    """
    Получить все роудмапы текущего пользователя по токену авторизации.
    
    Возвращает список роудмапов с целями и задачами для их достижения.
    
    **Требуется авторизация Bearer token**
    """
    return RoadmapsListResponse(
        roadmaps=roadmaps,
        total=len(roadmaps)
    )


@router.delete(
    "/{roadmap_id}",
    response_model=dict,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def delete_roadmap(
    roadmap_id: int = Path(..., gt=0, description="ID роудмапа для удаления"),
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Удалить выбранный роудмап текущего пользователя.
    
    Удаляет только те роудмапы, которые принадлежат авторизованному пользователю.
    
    **Требуется авторизация Bearer token**
    
    - **roadmap_id**: ID роудмапа для удаления (целое положительное число)
    """
    result = await delete_user_roadmap(roadmap_id, credentials, db)
    return result
