from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.infra.auth import API_KEY
from src.infra.database import get_db


@pytest_asyncio.fixture
async def client(db) -> AsyncIterator[AsyncClient]:
    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}
