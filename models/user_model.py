from pydantic import BaseModel
from typing import Optional


class UserSettingsResponse(BaseModel):
    """Response model for user settings operations"""
    success: bool
    message: str
    error: Optional[str] = None
