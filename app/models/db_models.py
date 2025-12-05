from sqlalchemy import Column, String, Text, DateTime, func
import uuid
from app.db.database import Base


class CollageSession(Base):
    __tablename__ = "collage_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slack_user_id = Column(Text, nullable=False)
    slack_channel_id = Column(Text, nullable=False)
    slack_thread_ts = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="awaiting_image1")
    image1_path = Column(Text, nullable=True)
    image2_path = Column(Text, nullable=True)
    output_path = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
