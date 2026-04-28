from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.auth import require_api_key
from src.infra.database import get_db
from src.routers.schemas.tasks import TaskCreate, TaskOut, TaskUpdate
from src.services import tasks as tasks_service

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post(
    "/projects/{project_id}/tasks/",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
)
async def create_task(project_id: int, body: TaskCreate, db: AsyncSession = Depends(get_db)):
    return await tasks_service.create_task(db, project_id, body)


@router.get(
    "/projects/{project_id}/tasks/",
    response_model=list[TaskOut],
    tags=["tasks"],
)
async def list_project_tasks(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await tasks_service.list_project_tasks(db, project_id, limit=limit, offset=offset)


@router.put("/tasks/{task_id}", response_model=TaskOut, tags=["tasks"])
async def update_task(task_id: int, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    return await tasks_service.update_task(db, task_id, body)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await tasks_service.delete_task(db, task_id)
