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
            variant="default"  # Move variant here if needed, but 'default' is already the default
        )

    # ------------------------------------------------------------------ #
    # Click handling
    # ------------------------------------------------------------------ #
    @on(Button.Pressed, "#btn")
    async def _on_button_pressed(self, _: Button.Pressed) -> None:
        """Open the file with the VSCode CLI."""
        self.post_message(self.Clicked(self._path, self._line, self._column))

        # Build the argument list for `code`
        arg = str(self._path)
        if self._line is not None:
            arg += f":{self._line}"
            if self._column is not None:
                arg += f":{self._column}"

        try:
            # `run_process` is non-blocking and works inside the container
            self.app.run_process(["code", arg])
            self.app.notify(f"Opened {self._path.name}", title="FileLink", timeout=1.5)
        except Exception as exc:  # pragma: no cover
            self.app.notify(
                f"Failed to open {self._path.name}: {exc}",
                severity="error",
                timeout=3,
            )