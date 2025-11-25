from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from textual import on, events
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.message import Message
from textual.containers import Horizontal

from .file_link import FileLink


class ToggleableFileLink(Widget):
    """A FileLink with an optional toggle (☐/✓) on the left and optional remove (×) on the right."""

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
    
    ToggleableFileLink .toggle-static {
        width: 3;
        min-width: 3;
        height: auto;
        background: transparent;
        border: none;
        padding: 0;
        color: $text;
        content-align: center middle;
    }
    
    ToggleableFileLink .toggle-static:hover {
        background: $boost;
    }
    
    ToggleableFileLink .file-link-container {
        width: 1fr;
        height: auto;
    }
    
    ToggleableFileLink .remove-static {
        width: 3;
        min-width: 3;
        height: auto;
        background: transparent;
        border: none;
        padding: 0;
        color: $error;
        content-align: center middle;
    }
    
    ToggleableFileLink .remove-static:hover {
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
        show_toggle: bool = True,
        show_remove: bool = True,
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
        show_toggle : bool
            Whether to display the toggle component (default: True).
        show_remove : bool
            Whether to display the remove component (default: True).
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
        self._show_toggle = show_toggle
        self._show_remove = show_remove
        self._line = line
        self._column = column
        self._command_builder = command_builder
        self._disable_on_untoggle = disable_on_untoggle

    def compose(self) -> ComposeResult:
        with Horizontal():
            if self._show_toggle:
                yield Static(
                    "✓" if self._is_toggled else "☐",
                    id="toggle",
                    classes="toggle-static",
                )
            yield FileLink(
                self._path,
                line=self._line,
                column=self._column,
                command_builder=self._command_builder,
                classes="file-link-container",
            )
            if self._show_remove:
                yield Static(
                    "×",
                    id="remove",
                    classes="remove-static",
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

    @on(events.Click, "#toggle")
    def _on_toggle_clicked(self, event: events.Click) -> None:
        """Handle toggle click (if shown)."""
        if not self._show_toggle:
            return
        event.stop()  # Prevent bubbling
        self._is_toggled = not self._is_toggled
        
        # Update static content
        toggle_static = self.query_one("#toggle", Static)
        toggle_static.update("✓" if self._is_toggled else "☐")
        
        # Update disabled state
        self._update_disabled_state()
        
        # Post message
        self.post_message(self.Toggled(self._path, self._is_toggled))

    @on(events.Click, "#remove")
    def _on_remove_clicked(self, event: events.Click) -> None:
        """Handle remove click (if shown)."""
        if not self._show_remove:
            return
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