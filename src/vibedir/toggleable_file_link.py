from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static
from textual.message import Message

from .file_link import FileLink

class ToggleableFileLink(Widget):
    """A FileLink with a toggle (✔/☐) on the left and remove (X) on the right."""

    DEFAULT_CSS = """
    ToggleableFileLink {
        layout: horizontal;
        height: auto;
        align: left middle;
        margin: 0 1;
    }
    ToggleableFileLink .toggle-button {
        width: 3;
        background: transparent;
        border: none;
        padding: 0;
        content-align: center middle;
    }
    ToggleableFileLink .toggle-button:hover {
        text-style: bold;
    }
    ToggleableFileLink .remove-button {
        width: 3;
        background: transparent;
        color: red;
        border: none;
        padding: 0;
        content-align: center middle;
    }
    ToggleableFileLink .remove-button:hover {
        text-style: bold;
        background: $error 20%;
    }
    ToggleableFileLink.disabled .file-link Button {
        color: $text-disabled;
        text-style: none;
    }
    """

    class Toggled(Message):
        """Posted when the toggle state changes."""
        def __init__(self, path: Path, is_toggled: bool) -> None:
            super().__init__()
            self.path = path
            self.is_toggled = is_toggled

    class Removed(Message):
        """Posted when the remove button is clicked."""
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    def __init__(
        self,
        path: Path | str,
        *,
        initial_toggle: bool = False,
        line: Optional[int] = None,
        column: Optional[int] = None,
        command_builder: Optional[Callable] = None,
        on_toggle: Optional[Callable] = None,
        on_remove: Optional[Callable] = None,
        disable_on_untoggle: bool = False,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._path = Path(path).resolve()
        self._is_toggled = initial_toggle
        self._line = line
        self._column = column
        self._command_builder = command_builder
        self._on_toggle = on_toggle
        self._on_remove = on_remove
        self._disable_on_untoggle = disable_on_untoggle
        self._update_classes()

    def compose(self) -> ComposeResult:
        yield Button(
            "✔" if self._is_toggled else "☐",
            id="toggle",
            classes="toggle-button",
            tooltip="Toggle selection",
        )
        yield FileLink(
            self._path,
            line=self._line,
            column=self._column,
            command_builder=self._command_builder,
            classes="file-link",
        )
        yield Button(
            "X",
            id="remove",
            classes="remove-button",
            tooltip="Remove file",
        )

    def _update_classes(self) -> None:
        if self._disable_on_untoggle and not self._is_toggled:
            self.add_class("disabled")
        else:
            self.remove_class("disabled")

    @on(Button.Pressed, "#toggle")
    async def _on_toggle_pressed(self, _: Button.Pressed) -> None:
        self._is_toggled = not self._is_toggled
        toggle_btn = self.query_one("#toggle", Button)
        toggle_btn.label = "✔" if self._is_toggled else "☐"
        self._update_classes()
        self.post_message(self.Toggled(self._path, self._is_toggled))
        if self._on_toggle:
            self._on_toggle(self._path, self._is_toggled)

    @on(Button.Pressed, "#remove")
    async def _on_remove_pressed(self, _: Button.Pressed) -> None:
        self.post_message(self.Removed(self._path))
        if self._on_remove:
            self._on_remove(self._path)
        else:
            # Default: Remove self from parent if in a container
            if self.parent:
                self.remove()

    @on(FileLink.Clicked)
    def _on_file_clicked(self, event: FileLink.Clicked) -> None:
        # Bubble up the event if needed
        if self._disable_on_untoggle and not self._is_toggled:
            event.stop()  # Prevent opening if disabled
        else:
            self.post_message(event)  # Re-post for parent handling