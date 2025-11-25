from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static
from textual.message import Message
from textual.containers import Horizontal

from .file_link import FileLink


class ToggleableFileLink(Widget):
    """A FileLink with a toggle (☐/✓) on the left and remove (×) on the right."""

    DEFAULT_CSS = """
    ToggleableFileLink {
        height: auto;
        width: 100%;
    }
    
    ToggleableFileLink Horizontal {
        height: auto;
        width: 100%;
        align: left middle;
    }
    
    ToggleableFileLink .toggle-btn {
        width: 3;
        min-width: 3;
        height: auto;
        min-height: 0;
        background: transparent;
        border: none;
        padding: 0;
        color: $text;
        content-align: center middle;
    }
    
    ToggleableFileLink .toggle-btn:hover {
        background: $boost;
    }
    
    ToggleableFileLink .file-link-container {
        width: 1fr;
        height: auto;
    }
    
    ToggleableFileLink .remove-btn {
        width: 3;
        min-width: 3;
        height: auto;
        min-height: 0;
        background: transparent;
        border: none;
        padding: 0;
        color: $error;
        content-align: center middle;
    }
    
    ToggleableFileLink .remove-btn:hover {
        background: $boost;
        color: $error;
    }
    
    ToggleableFileLink.disabled {
        opacity: 0.5;
    }
    
    ToggleableFileLink.disabled .file-link-container {
        text-style: dim;
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
        disable_on_untoggle: bool = False,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        path : Path | str
            Full path to the file.
        initial_toggle : bool
            Whether the item starts toggled (checked).
        line, column : int | None
            Optional cursor position to jump to.
        command_builder : Callable | None
            Function for opening the file.
        disable_on_untoggle : bool
            If True, dim/disable the link when untoggled.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._path = Path(path).resolve()
        self._is_toggled = initial_toggle
        self._line = line
        self._column = column
        self._command_builder = command_builder
        self._disable_on_untoggle = disable_on_untoggle

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button(
                "✓" if self._is_toggled else "☐",
                id="toggle",
                classes="toggle-btn",
                variant="default",
            )
            yield FileLink(
                self._path,
                line=self._line,
                column=self._column,
                command_builder=self._command_builder,
                classes="file-link-container",
            )
            yield Button(
                "×",
                id="remove",
                classes="remove-btn",
                variant="default",
            )

    def on_mount(self) -> None:
        """Update initial disabled state."""
        self._update_disabled_state()

    def _update_disabled_state(self) -> None:
        """Update the disabled class based on toggle state."""
        if self._disable_on_untoggle and not self._is_toggled:
            self.add_class("disabled")
        else:
            self.remove_class("disabled")

    @on(Button.Pressed, "#toggle")
    def _on_toggle_pressed(self, event: Button.Pressed) -> None:
        """Handle toggle button click."""
        event.stop()  # Prevent bubbling
        self._is_toggled = not self._is_toggled
        
        # Update button label
        toggle_btn = self.query_one("#toggle", Button)
        toggle_btn.label = "✓" if self._is_toggled else "☐"
        
        # Update disabled state
        self._update_disabled_state()
        
        # Post message
        self.post_message(self.Toggled(self._path, self._is_toggled))

    @on(Button.Pressed, "#remove")
    def _on_remove_pressed(self, event: Button.Pressed) -> None:
        """Handle remove button click."""
        event.stop()  # Prevent bubbling
        self.post_message(self.Removed(self._path))

    @on(FileLink.Clicked)
    def _on_file_clicked(self, event: FileLink.Clicked) -> None:
        """Handle file link click - prevent if disabled."""
        if self._disable_on_untoggle and not self._is_toggled:
            event.stop()
        # Otherwise let it bubble up

    @property
    def is_toggled(self) -> bool:
        """Get the current toggle state."""
        return self._is_toggled

    @property
    def path(self) -> Path:
        """Get the file path."""
        return self._path