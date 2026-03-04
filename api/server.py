"""
FastAPI server for anami-stream.

Mirrors anami-controller/api/server.py — create_app() configures CORS and
registers routes; start_api_background() runs uvicorn in a daemon thread.
"""

import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import __version__
from api.dependencies import init_components
from api.routes import stream_router, control_router, health_router
from capture.capture_manager import CaptureManager
from utils.logger import get_logger

logger = get_logger('API.Server')

app = None


def create_app(capture_manager: CaptureManager, config: dict) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        capture_manager: Initialized CaptureManager instance
        config:          Parsed config.yaml as a dict
    """
    init_components(capture_manager)

    api_app = FastAPI(
        title="Anami Stream API",
        description="MJPEG video streaming service for drone camera feed",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    cors_origins = (
        config.get('api', {}).get('cors_origins') or [
            "http://localhost:3000",
            "http://localhost:8080",
        ]
    )

    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_app.include_router(stream_router, prefix="/stream")
    api_app.include_router(control_router, prefix="/stream")
    api_app.include_router(health_router, prefix="/stream")

    logger.info("FastAPI app created and configured")
    return api_app


def start_api_server(
    capture_manager: CaptureManager,
    config: dict,
    host: str = "0.0.0.0",
    port: int = 8090,
):
    """Start uvicorn (blocking — run in a thread)."""
    global app
    app = create_app(capture_manager, config)

    logger.info(f"Starting stream server on http://{host}:{port}")
    logger.info(f"  - MJPEG stream:  http://{host}:{port}/stream/feed")
    logger.info(f"  - Snapshot:      http://{host}:{port}/stream/snapshot")
    logger.info(f"  - Health:        http://{host}:{port}/stream/health")
    logger.info(f"  - Config:        http://{host}:{port}/stream/config")
    logger.info(f"  - Docs:          http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )


def start_api_background(
    capture_manager: CaptureManager,
    config: dict,
    host: str = "0.0.0.0",
    port: int = 8090,
) -> threading.Thread:
    """Start API server in a daemon thread."""
    thread = threading.Thread(
        target=start_api_server,
        args=(capture_manager, config, host, port),
        name="APIServerThread",
        daemon=True,
    )
    thread.start()
    logger.info(f"API server started in background thread on port {port}")
    return thread
