#!/usr/bin/env python3
"""
vibedir – tiny Textual demo
Header: Status [icon]
Menu : [r] Rotate Status (works repeatedly)
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, ListView, ListItem
from textual.reactive import reactive


# ----------------------------------------------------------------------
# Status constants & icons
# ----------------------------------------------------------------------
class Status:
    NOT_CFG = "not configured"
    NOT_RUN = "not run"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED  = "failed"


ICONS = {
    Status.NOT_CFG: "⊘",
    Status.NOT_RUN: "❓",
    Status.RUNNING: "⏳",
    Status.SUCCESS: "✅",
    Status.FAILED : "❌",
}

STATUS_ORDER = [
    Status.NOT_CFG,
    Status.NOT_RUN,
    Status.RUNNING,
    Status.SUCCESS,
    Status.FAILED,
]


# ----------------------------------------------------------------------
# The TUI
# ----------------------------------------------------------------------
class SimpleTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #status { height: 3; background: $primary; color: $text; padding: 1; }
    #menu   { height: 1fr; }
    """

    status = reactive(Status.NOT_CFG)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(id="status")
        yield ListView(
            ListItem(Label(" [r] Rotate Status"), id="rotate"),
            id="menu",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_status()

    # ------------------------------------------------------------------
    # Render & refresh
    # ------------------------------------------------------------------
    def _render_status(self) -> str:
        return f"Status {ICONS[self.status]}"

    def _refresh_status(self) -> None:
        self.query_one("#status", Label).update(self._render_status())

    def watch_status(self, old: str, new: str) -> None:
        self._refresh_status()

    # ------------------------------------------------------------------
    # Core rotation logic – shared by menu and key binding
    # ------------------------------------------------------------------
    def _rotate_status(self) -> None:
        idx = STATUS_ORDER.index(self.status)
        self.status = STATUS_ORDER[(idx + 1) % len(STATUS_ORDER)]
        # Allow the same menu item to be selected again
        self.query_one("#menu", ListView).index = None

    # ------------------------------------------------------------------
    # Menu selection
    # ------------------------------------------------------------------
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id == "rotate":
            self._rotate_status()

    # ------------------------------------------------------------------
    # Direct 'r' key binding
    # ------------------------------------------------------------------
    BINDINGS = [("r", "rotate", "Rotate Status")]

    def action_rotate(self) -> None:
        """Called when the user presses 'r'."""
        self._rotate_status()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    SimpleTUI().run()