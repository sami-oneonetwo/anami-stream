"""
API dependencies for anami-stream.

Mirrors anami-controller/api/dependencies.py — provides FastAPI dependency
injection for the CaptureManager.
"""

from typing import Optional
from fastapi import HTTPException

from capture.capture_manager import CaptureManager

_capture_manager: Optional[CaptureManager] = None


def init_components(capture_manager: CaptureManager):
    """Store the CaptureManager instance for injection into route handlers."""
    global _capture_manager
    _capture_manager = capture_manager


def get_capture_manager() -> CaptureManager:
    """FastAPI dependency: returns the CaptureManager or raises 503."""
    if _capture_manager is None:
        raise HTTPException(status_code=503, detail="Capture system not initialized")
    return _capture_manager
