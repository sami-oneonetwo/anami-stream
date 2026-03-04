"""Request models for anami-stream API."""

from typing import Literal
from pydantic import BaseModel


class QualityRequest(BaseModel):
    quality: Literal['low', 'medium', 'high']
