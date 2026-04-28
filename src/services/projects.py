from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.models.project import Project
from src.routers.schemas.projects import ProjectCreate, ProjectUpdate


async def get_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project", project_id)
    return project


async def create_project(db: AsyncSession, body: ProjectCreate) -> Project:
    project = Project(**body.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(db: AsyncSession, project_id: int, body: ProjectUpdate) -> Project:
    project = await get_project(db, project_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: int) -> None:
    project = await get_project(db, project_id)
    await db.delete(project)
    await db.commit()
