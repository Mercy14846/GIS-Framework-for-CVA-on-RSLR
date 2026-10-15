from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from coastal_dss import __version__
from coastal_dss.api.routes import assessment, meta
from coastal_dss.core.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lagos Coastal Vulnerability DSS",
        version=__version__,
        description="RSLR, coastal vulnerability (CVI) and impact assessment for Lagos.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(meta.router, prefix="/api/v1", tags=["meta"])
    app.include_router(assessment.router, prefix="/api/v1", tags=["assessment"])
    return app


app = create_app()
