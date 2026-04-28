from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.exceptions import NotFoundError
from src.infra.database import Base, engine
from src.models.project import Project  # noqa: F401  (register mapper)
from src.models.task import Task  # noqa: F401  (register mapper)
from src.routers.projects import router as projects_router
from src.routers.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Projects & Tasks API", lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def _not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(projects_router)
app.include_router(tasks_router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
