import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.config import settings


class StorageService:
    """Handle file storage operations."""

    @staticmethod
    async def save_upload(file: UploadFile, session_id: uuid.UUID, image_num: int) -> str:
        """
        Save uploaded file to inputs directory.

        Args:
            file: Uploaded file
            session_id: Session UUID
            image_num: 1 or 2 for image1/image2

        Returns:
            Relative path to saved file
        """
        # Ensure directory exists
        settings.INPUTS_PATH.mkdir(parents=True, exist_ok=True)

        # Get file extension
        ext = Path(file.filename).suffix.lower() or ".jpg"
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"

        # Create filename
        filename = f"{session_id}_{image_num}{ext}"
        filepath = settings.INPUTS_PATH / filename

        # Save file
        async with aiofiles.open(filepath, "wb") as f:
            content = await file.read()
            await f.write(content)

        return f"inputs/{filename}"

    @staticmethod
    async def save_output(image_bytes: bytes, session_id: uuid.UUID) -> str:
        """
        Save processed collage to outputs directory.

        Args:
            image_bytes: PNG image bytes
            session_id: Session UUID

        Returns:
            Relative path to saved file
        """
        # Ensure directory exists
        settings.OUTPUTS_PATH.mkdir(parents=True, exist_ok=True)

        filename = f"{session_id}.png"
        filepath = settings.OUTPUTS_PATH / filename

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(image_bytes)

        return f"outputs/{filename}"

    @staticmethod
    def get_full_path(relative_path: str) -> Path:
        """Get full filesystem path from relative path."""
        return settings.UPLOADS_PATH / relative_path

    @staticmethod
    def get_public_url(relative_path: str) -> str:
        """Get public URL for a file."""
        return f"{settings.BASE_URL}/static/{relative_path}"

    @staticmethod
    def get_border_path(border_name: str = "default.png") -> Path:
        """Get path to a border asset."""
        return settings.BORDERS_PATH / border_name

    @staticmethod
    def list_borders() -> list[str]:
        """List available border designs."""
        if not settings.BORDERS_PATH.exists():
            return []
        return [f.name for f in settings.BORDERS_PATH.glob("*.png")]
