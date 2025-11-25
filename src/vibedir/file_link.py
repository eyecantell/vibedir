from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button
from textual.message import Message
import subprocess


class FileLink(Widget):
    """Clickable filename that opens the real file in VSCode (Dev Container)."""

    DEFAULT_CSS = """
    FileLink {
        layout: horizontal;
        height: auto;
        margin: 0 1;
    }
    FileLink > Button {
        background: transparent;
        color: $primary;           /* VSCode blue by default */
        text-style: underline;
        padding: 0 0;
        border: none;
        width: auto;
    }
    FileLink > Button:hover {
        text-style: bold underline;
    }
    """

    class Clicked(Message):
        """Posted when the link is activated."""

        def __init__(self, path: Path, line: Optional[int], column: Optional[int]) -> None:
            super().__init__()
            self.path = path
            self.line = line
            self.column = column

    def __init__(
        self,
        path: Path | str,
        *,
        line: Optional[int] = None,
        column: Optional[int] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        path : Path | str
            Full path **inside the container**.
        line, column : int | None
            Optional cursor position to jump to.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._path = Path(path).resolve()
        self._line = line
        self._column = column

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def compose(self) -> ComposeResult:
        yield Button(
            self._path.name,
            id="btn",
            tooltip=str(self._path),
            variant="default", 
        )

    # ------------------------------------------------------------------ #
    # Click handling
    # ------------------------------------------------------------------ #
    @on(Button.Pressed, "#btn")
    async def _on_button_pressed(self, _: Button.Pressed) -> None:
        """Open the file with the VSCode CLI."""
        # FIRST notification - verify method is called
        self.app.notify("🔵 Button clicked!", title="Debug", timeout=3)
        
        self.post_message(self.Clicked(self._path, self._line, self._column))

        # Try to get relative path from current working directory
        try:
            cwd = Path.cwd()
            relative_path = self._path.relative_to(cwd)
            file_arg = str(relative_path)
        except ValueError:
            file_arg = str(self._path)

        # Build the --goto argument with line:column if provided
        if self._line is not None:
            goto_arg = f"{file_arg}:{self._line}"
            if self._column is not None:
                goto_arg += f":{self._column}"
        else:
            goto_arg = file_arg

        # SECOND notification - show what we're trying to open
        self.app.notify(f"🟡 Opening: {goto_arg}", title="Debug", timeout=3)
        
        import os
        
        try:
            result = subprocess.run(
                ["code", "--goto", goto_arg],
                env=os.environ.copy(),
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                timeout=3
            )
            
            # THIRD notification - show result
            self.app.notify(f"🟢 Done! RC={result.returncode}", title="Debug", timeout=3)
            
        except subprocess.TimeoutExpired:
            self.app.notify("🔴 Timeout!", severity="error", timeout=3)
        except Exception as exc:
            self.app.notify(f"🔴 Error: {exc}", severity="error", timeout=3)