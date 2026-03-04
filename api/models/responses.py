"""Response models for anami-stream API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    uptime: float
    device_open: bool
    fps_actual: float


class StreamConfigResponse(BaseModel):
    quality: str
    resolution: str
    jpeg_quality: int
    device_index: int


class SuccessResponse(BaseModel):
    success: bool
    message: str = ""
