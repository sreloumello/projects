# app/main.py — fastapi application entrypoint + lambda handler

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.config import get_settings
from app.routers import auth, board, tasks, columns


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: nothing to do — db is managed by ansible
    yield
    # shutdown


def create_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title="Kanban Board API",
        description="kanban board with cognito auth — luan martins de mello",
        version="1.0.0",
        docs_url="/docs" if s.ENV == "dev" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[s.ALLOWED_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(auth.router)
    app.include_router(board.router)
    app.include_router(tasks.router)
    app.include_router(columns.router)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "healthy", "env": s.ENV}

    return app


app = FastAPI.__new__(FastAPI)
app = create_app()

# lambda handler via mangum
handler = Mangum(app, lifespan="off")
