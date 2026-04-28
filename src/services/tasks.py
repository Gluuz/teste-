from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.models.task import Task
from src.routers.schemas.tasks import TaskCreate, TaskUpdate
from src.services.projects import get_project


async def get_task(db: AsyncSession, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise NotFoundError("Task", task_id)
    return task


async def create_task(db: AsyncSession, project_id: int, body: TaskCreate) -> Task:
    await get_project(db, project_id)
    task = Task(project_id=project_id, **body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def list_project_tasks(
    db: AsyncSession, project_id: int, *, limit: int, offset: int
) -> list[Task]:
    await get_project(db, project_id)
    stmt = (
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.priority.desc(), Task.id.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task(db: AsyncSession, task_id: int, body: TaskUpdate) -> Task:
    task = await get_task(db, task_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> None:
    task = await get_task(db, task_id)
    await db.delete(task)
    await db.commit()
