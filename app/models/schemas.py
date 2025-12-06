from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    AWAITING_IMAGE1 = "awaiting_image1"
    AWAITING_IMAGE2 = "awaiting_image2"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionCreate(BaseModel):
    slack_user_id: str
    slack_channel_id: str
    slack_thread_ts: Optional[str] = None


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    image1_path: Optional[str] = None
    image2_path: Optional[str] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    slack_user_id: str
    slack_channel_id: str
    slack_thread_ts: Optional[str]
    status: SessionStatus
    image1_path: Optional[str]
    image2_path: Optional[str]
    output_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    success: bool
    path: str
    session_id: str


class ProcessRequest(BaseModel):
    session_id: str
    background_name: Optional[str] = None  # Optional specific background


class ProcessResponse(BaseModel):
    success: bool
    output_url: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    storage: str
