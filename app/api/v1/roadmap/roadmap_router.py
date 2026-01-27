from fastapi import APIRouter, Depends, HTTPException, status, Security, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.schemas.roadmap import RoadmapResponse, RoadmapsListResponse, TaskResponse
from app.schemas.goal import GoalUpdate
from app.services.roadmap.get_all_roadmap import get_user_roadmaps
from app.services.roadmap.get_all_task import get_tasks_for_roadmap
from app.services.roadmap.task_service import (
    create_task_for_roadmap,
    update_task_for_roadmap,
    delete_task_for_roadmap,
    set_task_complete_for_roadmap,
)
from app.services.roadmap.delete_one_roadmap import delete_user_roadmap
from app.services.roadmap.rename_goals import update_goal_in_roadmap
from app.models.roadmap import Roadmap
from app.models.task import Task
from app.services.user.get_my_user import get_current_user
from app.models.user import User
from app.schemas.roadmap import TaskCreate, TaskUpdate

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
    
    return RoadmapsListResponse(
        roadmaps=roadmaps,
        total=len(roadmaps)
    )


@router.get(
    "/{roadmap_id}/tasks",
    response_model=list[TaskResponse],
    openapi_extra={"security": [{"Bearer": []}]}
)
async def get_tasks_by_roadmap(
    roadmap_id: int = Path(..., gt=0, description="ID роудмапа"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tasks = await get_tasks_for_roadmap(db, int(current_user.user_id), roadmap_id)
    return tasks


@router.post(
    "/{roadmap_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def create_task(
    roadmap_id: int = Path(..., gt=0, description="ID роудмапа"),
    task_data: TaskCreate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await create_task_for_roadmap(
        db,
        int(current_user.user_id),
        roadmap_id,
        title=task_data.title,
        description=task_data.description,
        order_index=task_data.order_index,
        deadline_start=task_data.deadline_start,
        deadline_end=task_data.deadline_end,
    )
    return task


@router.put(
    "/{roadmap_id}/tasks/{task_id}",
    response_model=TaskResponse,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def update_task(
    roadmap_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    task_data: TaskUpdate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = task_data.model_dump(exclude_none=True)
    task = await update_task_for_roadmap(db, int(current_user.user_id), roadmap_id, task_id, data)
    return task


@router.delete(
    "/{roadmap_id}/tasks/{task_id}",
    response_model=dict,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def delete_task(
    roadmap_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_task_for_roadmap(db, int(current_user.user_id), roadmap_id, task_id)
    return {"status": "success", "message": "Task deleted"}


@router.patch(
    "/{roadmap_id}/tasks/{task_id}/complete",
    response_model=TaskResponse,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def set_task_complete(
    roadmap_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    completed: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await set_task_complete_for_roadmap(db, int(current_user.user_id), roadmap_id, task_id, completed)
    return task


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
    
    result = await delete_user_roadmap(roadmap_id, credentials, db)
    return result


@router.put(
    "/{roadmap_id}/goal",
    response_model=dict,
    openapi_extra={"security": [{"Bearer": []}]}
)
async def update_goal(
    roadmap_id: int = Path(..., gt=0, description="ID роудмапа"),
    goal_data: GoalUpdate = None,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
):
    
    result = await update_goal_in_roadmap(
        roadmap_id,
        goal_data.title,
        goal_data.description,
        credentials,
        db
    )
    return result
