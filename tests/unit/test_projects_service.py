from unittest.mock import AsyncMock, MagicMock

import pytest

from src.exceptions import NotFoundError
from src.models.project import Project
from src.routers.schemas.projects import ProjectCreate, ProjectUpdate
from src.services import projects as projects_service


def _mock_session(get_returns=None) -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock(return_value=get_returns)
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


async def test_get_project_raises_when_missing():
    db = _mock_session(get_returns=None)

    with pytest.raises(NotFoundError) as exc:
        await projects_service.get_project(db, 42)

    assert exc.value.resource == "Project"
    assert exc.value.identifier == 42
    db.get.assert_awaited_once_with(Project, 42)


async def test_get_project_returns_existing():
    project = Project(id=1, name="P")
    db = _mock_session(get_returns=project)

    assert await projects_service.get_project(db, 1) is project


async def test_create_project_persists_and_refreshes():
    db = _mock_session()
    body = ProjectCreate(name="P", description="d")

    result = await projects_service.create_project(db, body)

    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    assert result.name == "P"
    assert result.description == "d"


async def test_update_project_only_mutates_set_fields():
    project = Project(id=1, name="old", description="old-desc")
    db = _mock_session(get_returns=project)
    body = ProjectUpdate(description="new-desc")

    result = await projects_service.update_project(db, 1, body)

    assert result.name == "old"
    assert result.description == "new-desc"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(project)


async def test_update_project_raises_when_missing():
    db = _mock_session(get_returns=None)

    with pytest.raises(NotFoundError):
        await projects_service.update_project(db, 1, ProjectUpdate(name="x"))

    db.commit.assert_not_awaited()


async def test_delete_project_calls_session_delete():
    project = Project(id=1, name="P")
    db = _mock_session(get_returns=project)

    await projects_service.delete_project(db, 1)

    db.delete.assert_awaited_once_with(project)
    db.commit.assert_awaited_once()


async def test_delete_project_raises_when_missing():
    db = _mock_session(get_returns=None)

    with pytest.raises(NotFoundError):
        await projects_service.delete_project(db, 99)

    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
