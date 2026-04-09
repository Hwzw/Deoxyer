from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.routers import (
    constructs,
    genes,
    health,
    organisms,
    optimization,
    projects,
    proteins,
    regulatory,
)

TERMINAL_HTML = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "terminal.html"


def create_app() -> FastAPI:
    application = FastAPI(
        title="GenBit API",
        description="Synthetic Biology Construct Designer",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(genes.router, prefix="/api/genes", tags=["genes"])
    application.include_router(proteins.router, prefix="/api/proteins", tags=["proteins"])
    application.include_router(organisms.router, prefix="/api/organisms", tags=["organisms"])
    application.include_router(constructs.router, prefix="/api/constructs", tags=["constructs"])
    application.include_router(
        optimization.router, prefix="/api/optimization", tags=["optimization"]
    )
    application.include_router(regulatory.router, prefix="/api/regulatory", tags=["regulatory"])
    application.include_router(projects.router, prefix="/api/projects", tags=["projects"])

    @application.get("/", include_in_schema=False)
    async def serve_terminal():
        return FileResponse(TERMINAL_HTML, media_type="text/html")

    return application


app = create_app()
