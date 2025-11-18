import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import toml  # Import toml to load config

# Load config
CONFIG = toml.load("config.toml")
USER_ICON = CONFIG["prompt_icons"]["user"]
ASSISTANT_ICON = CONFIG["prompt_icons"]["assistant"]

class VibedirMessage:
    """Represents a single message in the vibedir prompt history."""
    def __init__(self, role: str, timestamp: Optional[str], content: str):
        self.role = role  # 'user', 'assistant', or 'pending'
        self.timestamp = timestamp
        self.content = content

    def to_markdown_header(self, model: str = "grok-4") -> str:
        """Generate the Markdown header for this message."""
        if self.timestamp is None:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        else:
            now = self.timestamp
        if self.role == 'user':
            return f"## {USER_ICON}User - {now}\n\n{self.content}\n\n"
        elif self.role == 'assistant':
            return f"## {ASSISTANT_ICON}Assistant ({model}) - {now}\n\n{self.content}\n\n"
        elif self.role == 'pending':
            return f"## {USER_ICON}Pending → (edit below)\n\n{self.content}\n"
        raise ValueError(f"Unknown role: {self.role}")

class VibedirPromptParser:
    """Parses and writes vibedir prompt.md files."""

    HEADER_PATTERN = re.compile(
        rf'^## ({re.escape(USER_ICON)}User|{re.escape(ASSISTANT_ICON)}Assistant \(.+?\)|{re.escape(USER_ICON)}Pending → .+) - (\d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}:\d{{2}}\.\d{{1,3}})$'
    )

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def parse(self) -> tuple[List[VibedirMessage], Optional[VibedirMessage]]:
        """Parse file into history messages and pending."""
        if not self.file_path.exists():
            return [], None

        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        messages: List[VibedirMessage] = []
        current_role = None
        current_timestamp: Optional[str] = None
        current_content: List[str] = []

        for line in lines:
            line = line.rstrip('\n')
            match = self.HEADER_PATTERN.match(line)
            if match:
                if current_role is not None:
                    messages.append(VibedirMessage(current_role, current_timestamp, '\n'.join(current_content).strip()))
                header_text, timestamp = match.groups()
                if 'User' in header_text:
                    current_role = 'user'
                elif 'Assistant' in header_text:
                    current_role = 'assistant'
                elif 'Pending' in header_text:
                    current_role = 'pending'
                current_timestamp = timestamp
                current_content = []
                # Skip the expected blank line after header
                continue
            current_content.append(line)

        if current_role is not None:
            messages.append(VibedirMessage(current_role, current_timestamp, '\n'.join(current_content).strip()))

        # Separate pending
        pending = None
        history = []
        for msg in messages:
            if msg.role == 'pending':
                pending = msg
            else:
                history.append(msg)

        if pending is None:
            self._append_pending()
            return self.parse()

        return history, pending

    def write_pending(self, pending_text: str):
        """Update only the pending section."""
        history, _ = self.parse()
        now = datetime.now().isoformat(timespec='milliseconds')
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(f"# vibedir session - {now}\n\n")
            for msg in history:
                f.write(msg.to_markdown_header())
            f.write(VibedirMessage('pending', None, pending_text).to_markdown_header())

    def append_message(self, role: str, content: str, model: str = "grok-4"):
        """Append a new user or assistant message and fresh pending."""
        with open(self.file_path, 'a', encoding='utf-8') as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
            msg = VibedirMessage(role, now, content)
            f.write(msg.to_markdown_header(model=model))
            f.write(VibedirMessage('pending', None, "").to_markdown_header())

    def remove_message(self, index: int):
        """Remove a message from history by index (0-based)."""
        history, pending = self.parse()
        if 0 <= index < len(history):
            del history[index]
            now = datetime.now().isoformat(timespec='milliseconds')
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(f"# vibedir session - {now}\n\n")
                for msg in history:
                    f.write(msg.to_markdown_header())
                if pending:
                    f.write(pending.to_markdown_header())

    def _append_pending(self):
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(VibedirMessage('pending', None, "").to_markdown_header())

    def init_file(self):
        """Create file if missing."""
        if not self.file_path.exists():
            now = datetime.now().isoformat(timespec='milliseconds')
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(f"# vibedir session - {now}\n\n")
                f.write(VibedirMessage('pending', None, "").to_markdown_header())