from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal  # Import for robust horizontal layout
from textual.message import Message
from textual.widgets import Button

from .file_link import FileLink  # Assuming this is your attached FileLink

class ToggleableFileLink(Horizontal):  # Inherit from Horizontal for better layout control
    """A FileLink with a toggle (☐/✔) on the left and remove (X) on the right."""

    DEFAULT_CSS = """
    ToggleableFileLink {
        height: 1;     # Constrain to single line to mask shifts and fit compact use
        width: auto;   # Size to content, prevent stretching
        align: center middle;  # Ensure vertical centering
        overflow-x: auto;  # Scroll if filename is too long
        background: $panel;  # Subtle background for overall contrast if text is blending
    }
    ToggleableFileLink > * {
        margin: 0;  # Remove all default margins on children for tight control
        padding: 0; # Remove all paddings for tighter spacing
        height: 1;  # Force all children to single-line height
    }
    ToggleableFileLink .toggle-button {
        width: 2;  # Fixed width to prevent shifting
        background: transparent;
        border: none;
        content-align: center middle;  # Explicit centering
        color: white;  # Force visibility
    }
    ToggleableFileLink .toggle-button:hover {
        /* No styles - prevent any changes that could "hide" the symbol */
    }
    ToggleableFileLink .file-link {
        width: auto;  # Size to filename content
    }
    ToggleableFileLink .file-link > Button {
        padding: 0;   # No extra padding
        content-align: center middle;  # Center text vertically
        color: white !important;  # Force high-contrast color to override theme/background blending
        background: transparent;  # Ensure no background hides text
    }
    ToggleableFileLink .remove-button {
        width: 1;  # Tight width for single char
        background: transparent;
        color: red;  # Fixed visible red
        border: none;
        content-align: center middle;  # Explicit centering to prevent shifts
    }
    ToggleableFileLink .remove-button:hover {
        /* No styles - prevent any changes that could "hide" the symbol */
    }
    ToggleableFileLink.disabled .file-link Button {
        color: gray !important;  # Explicit gray but visible, override any dimming
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
        self.can_focus_children = True  # Allow tab focus to children (checkbox, etc.)
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
            # No tooltip
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

    def on_mount(self) -> None:
        # Force refresh after mounting to ensure initial state renders correctly
        toggle = self.query_one("#toggle", Button)
        toggle.label = "✔" if self._is_toggled else "☐"
        toggle.refresh()
        self.refresh()  # Full widget refresh for visibility

    def _update_classes(self) -> None:
        if self._disable_on_untoggle and not self._is_toggled:
            self.add_class("disabled")
        else:
            self.remove_class("disabled")
        self.refresh()  # Refresh on state change

    @on(Button.Pressed, "#toggle")
    async def _on_toggle_pressed(self, _: Button.Pressed) -> None:
        self._is_toggled = not self._is_toggled
        toggle_btn = self.query_one("#toggle", Button)
        toggle_btn.label = "✔" if self._is_toggled else "☐"
        self._update_classes()
        self.post_message(self.Toggled(self._path, self._is_toggled))
        if self._on_toggle:
            self._on_toggle(self._path, self._is_toggled)
        toggle_btn.refresh()  # Ensure visual update

    @on(Button.Pressed, "#remove")
    async def _on_remove_pressed(self, _: Button.Pressed) -> None:
        self.post_message(self.Removed(self._path))
        if self._on_remove:
            self._on_remove(self._path)

    @on(FileLink.Clicked)
    def _on_file_clicked(self, event: FileLink.Clicked) -> None:
        # Bubble up the event if needed
        if self._disable_on_untoggle and not self._is_toggled:
            event.stop()  # Prevent opening if disabled
        else:
            self.post_message(event)  # Re-post for parent handling