from unittest.mock import AsyncMock, MagicMock

import pytest

from src.exceptions import NotFoundError
from src.models.project import Project
from src.models.task import Task
from src.routers.schemas.tasks import TaskCreate, TaskUpdate
from src.services import tasks as tasks_service


def _mock_session(get_side_effect=None, get_returns=None) -> AsyncMock:
    session = AsyncMock()
    if get_side_effect is not None:
        session.get = AsyncMock(side_effect=get_side_effect)
    else:
        session.get = AsyncMock(return_value=get_returns)
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


async def test_get_task_raises_when_missing():
    db = _mock_session(get_returns=None)

    with pytest.raises(NotFoundError) as exc:
        await tasks_service.get_task(db, 7)

    assert exc.value.resource == "Task"
    assert exc.value.identifier == 7


async def test_create_task_requires_existing_project():
    db = _mock_session(get_side_effect=[None])  # project lookup returns None
    body = TaskCreate(title="t", priority=3)

    with pytest.raises(NotFoundError) as exc:
        await tasks_service.create_task(db, 99, body)

    assert exc.value.resource == "Project"
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


async def test_create_task_persists_under_project():
    project = Project(id=1, name="P")
    db = _mock_session(get_side_effect=[project])
    body = TaskCreate(title="t", priority=5, completed=False)

    result = await tasks_service.create_task(db, 1, body)

    assert result.project_id == 1
    assert result.title == "t"
    assert result.priority == 5
    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)


async def test_update_task_only_mutates_set_fields():
    task = Task(id=1, project_id=1, title="t", priority=1, completed=False)
    db = _mock_session(get_returns=task)
    body = TaskUpdate(completed=True)

    result = await tasks_service.update_task(db, 1, body)

    assert result.title == "t"
    assert result.priority == 1
    assert result.completed is True
    db.commit.assert_awaited_once()


async def test_update_task_raises_when_missing():
    db = _mock_session(get_returns=None)

    with pytest.raises(NotFoundError):
        await tasks_service.update_task(db, 1, TaskUpdate(completed=True))

    db.commit.assert_not_awaited()


async def test_delete_task_calls_session_delete():
    task = Task(id=1, project_id=1, title="t", priority=1, completed=False)
    db = _mock_session(get_returns=task)

    await tasks_service.delete_task(db, 1)

    db.delete.assert_awaited_once_with(task)
    db.commit.assert_awaited_once()
