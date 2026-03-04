"""Quality control route."""

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_capture_manager
from api.models.requests import QualityRequest
from api.models.responses import SuccessResponse
from capture.capture_manager import CaptureManager

router = APIRouter()


@router.post("/quality", response_model=SuccessResponse)
async def set_quality(
    body: QualityRequest,
    cm: CaptureManager = Depends(get_capture_manager),
):
    try:
        cm.set_quality(body.quality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SuccessResponse(success=True, message=f"Quality set to {body.quality}")
