
import json
import logging
from typing import Dict, Set
from dynaconf import Dynaconf  # Assuming we import from config.py's setup

logger = logging.getLogger(__name__)

class CommandStatus:
    """Manages command statuses and configurable icons."""
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    WAITING = "waiting"  
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    # Default icons (from your snippet, with additions for completeness)
    DEFAULT_ICONS: Dict[str, str] = {
        NOT_CONFIGURED: "⚠️",
        NOT_RUN: "❓",
        WAITING: "⏳",
        RUNNING: "spinner",  # As per vibedir.md for animated cases
        SUCCESS: "✅",
        FAILED: "❌",
    }

    def __init__(self):
        self.icons: Dict[str, str] = self.DEFAULT_ICONS.copy()
        logger.debug("Command status icon defaults are " + json.dumps(self.icons))
        self._load_from_config()

    def _load_from_config(self) -> None:
        """Load icon overrides from config.toml [status_icons] using Dynaconf."""
        from ..config import load_config  # Import here to avoid circular deps
        settings: Dynaconf = load_config(namespace="vibedir", quiet=True)
        status_icons = settings.get("status_icons", {})
        for status, icon in status_icons.items():
            if status in self.DEFAULT_ICONS:
                self.icons[status] = icon
                logger.debug(f"Overriding icon for status '{status}' to '{icon}' from config.toml")
            else:
                # Log warning if unknown status (via config's logger)
                logger.warning(f"Unknown status '{status}' in config.toml – ignoring icon override.")
        
        logger.debug("Command status icon loaded are " + json.dumps(self.icons))

    def get_icon(self, status: str) -> str:
        """Get icon for a status, falling back to default if not overridden."""
        if status not in self.icons:
            raise ValueError(f"Invalid status: {status}")
        return self.icons[status]

    @classmethod
    def valid_statuses(cls) -> Set[str]:
        """Return a set of all valid status strings."""
        return {
            cls.NOT_CONFIGURED,
            cls.NOT_RUN,
            cls.WAITING,
            cls.RUNNING,
            cls.SUCCESS,
            cls.FAILED,
        }
    
# Usage: Module-level instance for easy access
command_status = CommandStatus()
logger.debug("Initialized global CommandStatus instance with icons: " + json.dumps(command_status.icons))