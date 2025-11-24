import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, field_validator, Field, ConfigDict

logger = logging.getLogger(__name__)

class Attachment(BaseModel):  
    """Base model for attachments in Vibedir history."""
    model_config = ConfigDict(frozen=True)  # Immutable

    type: Literal["file", "command"]
    path: Path
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        """Validate and normalize path, checking existence."""
        if not v.exists():
            logger.warning(f"Path does not exist: {v} – proceeding without validation.")
            # Or raise if strict
        return v.resolve()

class FileAttachment(Attachment):
    """Attachment for files, with original path and hash for dedup."""
    type: Literal["file"] = "file"
    original_path: Optional[Path] = None
    hash: Optional[str] = None  # SHA256 hex digest