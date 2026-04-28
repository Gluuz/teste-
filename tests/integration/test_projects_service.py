from datetime import datetime

import pytest

from src.exceptions import NotFoundError
from src.routers.schemas.projects import ProjectCreate, ProjectUpdate
from src.services import projects as projects_service

pytestmark = pytest.mark.integration


async def test_create_then_get_round_trip(db):
    created = await projects_service.create_project(
        db, ProjectCreate(name="Apollo", description="moon")
    )

    assert created.id is not None
    assert isinstance(created.created_at, datetime)

    fetched = await projects_service.get_project(db, created.id)
    assert fetched.id == created.id
    assert fetched.name == "Apollo"
    assert fetched.description == "moon"


async def test_get_missing_raises_not_found(db):
    with pytest.raises(NotFoundError):
        await projects_service.get_project(db, 999_999)


async def test_update_only_applies_set_fields(db):
    project = await projects_service.create_project(
        db, ProjectCreate(name="orig", description="orig-desc")
    )

    updated = await projects_service.update_project(
        db, project.id, ProjectUpdate(description="new-desc")
    )

    assert updated.name == "orig"
    assert updated.description == "new-desc"


async def test_delete_removes_row(db):
    project = await projects_service.create_project(db, ProjectCreate(name="del"))
    await projects_service.delete_project(db, project.id)

    with pytest.raises(NotFoundError):
        await projects_service.get_project(db, project.id)


async def test_delete_missing_raises(db):
    with pytest.raises(NotFoundError):
        await projects_service.delete_project(db, 999_999)
