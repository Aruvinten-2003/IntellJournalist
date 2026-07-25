"""FastAPI application entry point for Intell Journalist."""

import importlib
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import (
    close_database_connection,
    connect_to_database,
    database_health,
    database_is_connected,
)


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage database startup and shutdown for the application."""
    try:
        await connect_to_database()
    except Exception:
        if settings.database_required or settings.is_production:
            raise
        logger.warning(
            "Starting without MongoDB. API routes that need the database will be unavailable."
        )

    yield

    await close_database_connection()


def _include_available_routers(app: FastAPI) -> None:
    """Register route modules once they expose an APIRouter named `router`."""
    route_specs = (
        ("auth", "/auth", ["Authentication"]),
        ("news", "/news", ["News"]),
        ("chat", "/chat", ["Chat"]),
    )

    for module_name, prefix, tags in route_specs:
        try:
            module = importlib.import_module(f".routes.{module_name}", package=__package__)
        except Exception as exc:
            logger.warning(
                "Route module '%s' is not ready and was skipped: %s",
                module_name,
                exc,
            )
            continue

        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            app.include_router(router, prefix=f"{settings.api_prefix}{prefix}", tags=tags)
        else:
            logger.info(
                "Route module '%s' has no APIRouter instance named 'router'; skipping it",
                module_name,
            )


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(f"{settings.api_prefix}/health", tags=["System"])
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "application": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "database": await database_health(),
        }

    @app.get("/health", include_in_schema=False)
    async def simple_health() -> dict[str, Any]:
        return {
            "status": "ok",
            "database_connected": database_is_connected(),
        }

    _include_available_routers(app)

    frontend = settings.frontend_directory
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    else:
        logger.warning("Frontend directory does not exist: %s", frontend)

        @app.get("/", include_in_schema=False)
        async def root() -> dict[str, str]:
            return {"message": settings.app_name}

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
