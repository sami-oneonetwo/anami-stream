from api.routes.stream import router as stream_router
from api.routes.control import router as control_router
from api.routes.health import router as health_router

__all__ = ["stream_router", "control_router", "health_router"]
