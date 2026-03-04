"""Health and config routes."""

from fastapi import APIRouter, Depends

from api.dependencies import get_capture_manager
from api.models.responses import HealthResponse, StreamConfigResponse
from capture.capture_manager import CaptureManager

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def get_health(cm: CaptureManager = Depends(get_capture_manager)):
    return HealthResponse(
        status="ok" if cm.device_open else "degraded",
        uptime=round(cm.uptime, 1),
        device_open=cm.device_open,
        fps_actual=cm.get_fps_actual(),
    )


@router.get("/api/config", response_model=StreamConfigResponse)
async def get_config(cm: CaptureManager = Depends(get_capture_manager)):
    return StreamConfigResponse(
        quality=cm.quality,
        resolution=cm.resolution,
        jpeg_quality=cm.jpeg_quality,
        device_index=cm.device_index,
    )
