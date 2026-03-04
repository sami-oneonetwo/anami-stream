"""
MJPEG stream and snapshot routes.

GET /stream    — multipart/x-mixed-replace MJPEG stream (works as <img src>)
GET /snapshot  — single JPEG frame download
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse

from api.dependencies import get_capture_manager
from capture.capture_manager import CaptureManager

router = APIRouter()

_FRAME_INTERVAL = 1 / 30  # 30fps cap — consumers see whatever the device produces


@router.get("/stream")
async def mjpeg_stream(cm: CaptureManager = Depends(get_capture_manager)):
    """
    MJPEG multipart stream.

    Browsers can consume this directly as <img src="/stream">.
    Latency is sub-second; no JavaScript decoder required.
    """
    async def generate():
        while True:
            frame = cm.get_latest_frame()
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )
            await asyncio.sleep(_FRAME_INTERVAL)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/snapshot")
async def snapshot(cm: CaptureManager = Depends(get_capture_manager)):
    """Return the latest frame as a single JPEG."""
    frame = cm.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available")
    return Response(
        content=frame,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"},
    )
