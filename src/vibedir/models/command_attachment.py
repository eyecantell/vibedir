import json
import re
import logging
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator, Field
from .attachment import Attachment
from .command_status import CommandStatus, command_status  # Import the instance

logger = logging.getLogger(__name__)

class CommandAttachment(Attachment):
    """Model for command attachments, including status and output handling."""
    type: Literal["command"] = "command"
    name: str
    status: str  # Will validate against valid statuses from CommandStatus
    output: Optional[str] = None
    success_value: Optional[bool] = None
    output_path: Optional[Path] = None
    output_format: str = "txt"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = CommandStatus.valid_statuses()
        if v not in valid:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid}")
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        # Allow alphanumeric + dots/hyphens, no special fs chars
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError(f"Invalid output_format: {v}. Must be alphanumeric with . or - only.")
        if len(v) > 40 or len(v) == 0:  # Arbitrary limits for sanity
            raise ValueError(f"Invalid output_format length: {len(v)}")
        return v.lower()  # Normalize to lowercase

    def compute_output_path(self) -> Path:
        if self.path.suffix == ".json":
            return self.path.with_name(f"{self.path.stem}_output.{self.output_format}")
        raise ValueError("Invalid base path for output")

    def get_status_icon(self) -> str:
        """Convenience: Get icon via global status instance."""
        
        logger.debug("Global CommandStatus instance (command_status) has icons: " + json.dumps(command_status.icons))
        return command_status.get_icon(self.status)
    

model_config = ConfigDict(frozen=True)