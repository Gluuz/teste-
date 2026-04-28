from datetime import date

import pytest
from sqlalchemy import select

from src.exceptions import NotFoundError
from src.models.task import Task
from src.routers.schemas.projects import ProjectCreate
from src.routers.schemas.tasks import TaskCreate, TaskUpdate
from src.services import projects as projects_service
from src.services import tasks as tasks_service

pytestmark = pytest.mark.integration


async def _make_project(db, name: str = "P"):
    return await projects_service.create_project(db, ProjectCreate(name=name))


async def test_create_task_under_project(db):
    project = await _make_project(db)

    task = await tasks_service.create_task(
        db,
        project.id,
        TaskCreate(title="t", priority=3, due_date=date(2026, 5, 1)),
    )

    assert task.id is not None
    assert task.project_id == project.id
    assert task.priority == 3
    assert task.completed is False
    assert task.due_date == date(2026, 5, 1)


async def test_create_task_under_missing_project_raises(db):
    with pytest.raises(NotFoundError) as exc:
        await tasks_service.create_task(db, 999_999, TaskCreate(title="t"))

    assert exc.value.resource == "Project"


async def test_list_tasks_sorted_by_priority_desc(db):
    project = await _make_project(db)
    for title, priority in [("low", 1), ("high", 10), ("mid", 5)]:
        await tasks_service.create_task(db, project.id, TaskCreate(title=title, priority=priority))

    listed = await tasks_service.list_project_tasks(db, project.id, limit=50, offset=0)

    assert [t.priority for t in listed] == [10, 5, 1]
    assert [t.title for t in listed] == ["high", "mid", "low"]


async def test_list_tasks_pagination(db):
    project = await _make_project(db)
    for i in range(5):
        await tasks_service.create_task(db, project.id, TaskCreate(title=f"t{i}", priority=i))

    page1 = await tasks_service.list_project_tasks(db, project.id, limit=2, offset=0)
    page2 = await tasks_service.list_project_tasks(db, project.id, limit=2, offset=2)

    assert [t.priority for t in page1] == [4, 3]
    assert [t.priority for t in page2] == [2, 1]


async def test_list_tasks_for_missing_project_raises(db):
    with pytest.raises(NotFoundError):
        await tasks_service.list_project_tasks(db, 999_999, limit=10, offset=0)


async def test_update_task_partial(db):
    project = await _make_project(db)
    task = await tasks_service.create_task(db, project.id, TaskCreate(title="t", priority=1))

    updated = await tasks_service.update_task(db, task.id, TaskUpdate(completed=True))

    assert updated.completed is True
    assert updated.title == "t"
    assert updated.priority == 1


async def test_delete_task(db):
    project = await _make_project(db)
    task = await tasks_service.create_task(db, project.id, TaskCreate(title="t", priority=1))

    await tasks_service.delete_task(db, task.id)

    with pytest.raises(NotFoundError):
        await tasks_service.get_task(db, task.id)


async def test_deleting_project_cascades_tasks(db):
    project = await _make_project(db)
    await tasks_service.create_task(db, project.id, TaskCreate(title="a", priority=1))
    await tasks_service.create_task(db, project.id, TaskCreate(title="b", priority=2))

    await projects_service.delete_project(db, project.id)

    remaining = (
        (await db.execute(select(Task).where(Task.project_id == project.id))).scalars().all()
    )
    assert remaining == []
