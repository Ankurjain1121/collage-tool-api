from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from app.db.database import get_db
from app.models.db_models import CollageSession
from app.models.schemas import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionStatus,
    UploadResponse,
    ProcessRequest,
    ProcessResponse,
)
from app.services.storage import StorageService
from app.services.compositor import CompositorService
from app.config import settings

router = APIRouter(prefix="/api/collage", tags=["collage"])


@router.post("/session", response_model=SessionResponse)
def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new collage session for a Slack user."""
    # Check if user already has an active session
    existing = db.query(CollageSession).filter(
        and_(
            CollageSession.slack_user_id == session_data.slack_user_id,
            CollageSession.status.in_(["awaiting_image1", "awaiting_image2", "processing"])
        )
    ).first()

    if existing:
        # Return existing active session
        return existing

    # Create new session
    session = CollageSession(
        slack_user_id=session_data.slack_user_id,
        slack_channel_id=session_data.slack_channel_id,
        slack_thread_ts=session_data.slack_thread_ts,
        status=SessionStatus.AWAITING_IMAGE1.value
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/session/{slack_user_id}", response_model=Optional[SessionResponse])
def get_session(slack_user_id: str, db: Session = Depends(get_db)):
    """Get the current active session for a Slack user."""
    session = db.query(CollageSession).filter(
        and_(
            CollageSession.slack_user_id == slack_user_id,
            CollageSession.status.in_(["awaiting_image1", "awaiting_image2", "processing"])
        )
    ).order_by(CollageSession.created_at.desc()).first()

    return session


@router.get("/session/id/{session_id}", response_model=SessionResponse)
def get_session_by_id(session_id: str, db: Session = Depends(get_db)):
    """Get a session by its ID."""
    session = db.query(CollageSession).filter(
        CollageSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    slack_user_id: str = Form(...),
    image_num: int = Form(...),  # 1 or 2
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an image for the collage.

    - image_num=1: Product closeup
    - image_num=2: Color variants

    Images can be uploaded in any order.
    """
    if image_num not in [1, 2]:
        raise HTTPException(status_code=400, detail="image_num must be 1 or 2")

    # Get active session (allow any status that isn't completed/failed)
    session = db.query(CollageSession).filter(
        and_(
            CollageSession.slack_user_id == slack_user_id,
            CollageSession.status.in_(["awaiting_image1", "awaiting_image2"])
        )
    ).order_by(CollageSession.created_at.desc()).first()

    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    # Save file (allow uploading in any order)
    storage = StorageService()
    relative_path = await storage.save_upload(file, session.id, image_num)

    # Update session
    if image_num == 1:
        session.image1_path = relative_path
        # If image2 already uploaded, stay at awaiting_image2, else move to it
        if session.status == SessionStatus.AWAITING_IMAGE1.value:
            session.status = SessionStatus.AWAITING_IMAGE2.value
    else:
        session.image2_path = relative_path
        # If image1 not uploaded yet, keep status as awaiting_image1
        # Otherwise keep as awaiting_image2 (ready for processing)

    db.commit()
    db.refresh(session)

    return UploadResponse(
        success=True,
        path=relative_path,
        session_id=session.id
    )


@router.post("/process", response_model=ProcessResponse)
async def process_collage(
    request: ProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Process the collage for a session.

    Both images must be uploaded before calling this.
    """
    session = db.query(CollageSession).filter(
        CollageSession.id == str(request.session_id)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.image1_path or not session.image2_path:
        raise HTTPException(status_code=400, detail="Both images must be uploaded first")

    # Update status to processing
    session.status = SessionStatus.PROCESSING.value
    db.commit()

    try:
        # Create collage (async - uses Replicate API for BG removal)
        compositor = CompositorService()
        output_bytes = await compositor.create_collage(
            session.image1_path,
            session.image2_path,
            background_name=request.background_name
        )

        # Save output
        storage = StorageService()
        output_path = await storage.save_output(output_bytes, session.id)
        output_url = storage.get_public_url(output_path)

        # Update session
        session.output_path = output_path
        session.status = SessionStatus.COMPLETED.value
        db.commit()

        return ProcessResponse(success=True, output_url=output_url)

    except Exception as e:
        session.status = SessionStatus.FAILED.value
        session.error_message = str(e)
        db.commit()
        return ProcessResponse(success=False, error=str(e))


@router.delete("/session/{session_id}")
def cancel_session(session_id: str, db: Session = Depends(get_db)):
    """Cancel/delete a session."""
    session = db.query(CollageSession).filter(
        CollageSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"success": True, "message": "Session cancelled"}


@router.get("/borders")
def list_borders():
    """List available border designs."""
    storage = StorageService()
    borders = storage.list_borders()
    return {"borders": borders}


@router.get("/backgrounds")
def list_backgrounds():
    """List available base backgrounds."""
    return {
        "backgrounds": settings.BASE_BACKGROUNDS,
        "overlays": [
            {"rgb": rgb, "name": name}
            for rgb, name in settings.SOLID_OVERLAYS
        ]
    }
