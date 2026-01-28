from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from operant.app.api.v1 import auth, organizations, projects, tasks, users
from operant.app.core.config import settings
from operant.app.core.errors import DomainError


def create_app() -> FastAPI:
    app = FastAPI(title="Operant API", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "env": settings.env}

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    # router wiring
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(organizations.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    return app


app = create_app()


