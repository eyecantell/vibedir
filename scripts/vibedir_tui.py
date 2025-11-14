#!/usr/bin/env python3
"""
vibedir – tiny Textual demo with configurable icons
"""

import pathlib
from typing import Dict

import tomli  # pip install tomli (or tomllib in Python 3.11+)
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, ListView, ListItem
from textual.reactive import reactive


# ----------------------------------------------------------------------
# 1. Status constants (internal keys)
# ----------------------------------------------------------------------
class Status:
    NOT_CFG = "not_configured"
    NOT_RUN = "not_run"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED  = "failed"


# ----------------------------------------------------------------------
# 2. Default icons
# ----------------------------------------------------------------------
DEFAULT_ICONS: Dict[str, str] =  {
    Status.NOT_CFG: "⊘",
    Status.NOT_RUN: "❓",
    Status.RUNNING: "⏳",
    Status.SUCCESS: "✅",
    Status.FAILED : "❌",
}

# ----------------------------------------------------------------------
# 3. Load icons from config.toml (if it exists)
# ----------------------------------------------------------------------
CONFIG_PATH = pathlib.Path(".vibedir/config.toml")

def load_icons() -> Dict[str, str]:
    """Return a dict of status → icon, merging config with defaults."""
    icons = DEFAULT_ICONS.copy()

    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("rb") as f:
                cfg = tomli.load(f)
            cfg_icons = cfg.get("icons", {})
            # Map config keys → internal keys
            mapping = {
                "not_configured": Status.NOT_CFG,
                "not_run":        Status.NOT_RUN,
                "running":        Status.RUNNING,
                "success":        Status.SUCCESS,
                "failed":         Status.FAILED,
            }
            for cfg_key, internal_key in mapping.items():
                if cfg_key in cfg_icons:
                    icons[internal_key] = cfg_icons[cfg_key]
        except Exception as exc:          # pragma: no cover
            print(f"[vibedir] warning: could not read icons: {exc}")

    return icons


ICONS = load_icons()


# ----------------------------------------------------------------------
# 4. Rotation order
# ----------------------------------------------------------------------
STATUS_ORDER = [
    Status.NOT_CFG,
    Status.NOT_RUN,
    Status.RUNNING,
    Status.SUCCESS,
    Status.FAILED,
]


# ----------------------------------------------------------------------
# 5. The TUI
# ----------------------------------------------------------------------
class SimpleTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #status { height: 3; background: $primary; color: $text; padding: 1; }
    #menu   { height: 1fr; }
    """

    status = reactive(Status.NOT_CFG)

    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(id="status")                     # no content yet
        yield ListView(
            ListItem(Label(" [r] Rotate Status"), id="rotate"),
            id="menu",
        )
        yield Footer()

    # ------------------------------------------------------------------
    def on_mount(self) -> None:
        self._refresh_status()

    # ------------------------------------------------------------------
    def _render_status(self) -> str:
        return f"Status {ICONS[self.status]}"

    def _refresh_status(self) -> None:
        self.query_one("#status", Label).update(self._render_status())

    def watch_status(self, _: str, __: str) -> None:
        self._refresh_status()

    # ------------------------------------------------------------------
    # Core rotation – used by menu **and** key binding
    # ------------------------------------------------------------------
    def _rotate_status(self) -> None:
        idx = STATUS_ORDER.index(self.status)
        self.status = STATUS_ORDER[(idx + 1) % len(STATUS_ORDER)]
        self.query_one("#menu", ListView).index = None

    # ------------------------------------------------------------------
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id == "rotate":
            self._rotate_status()

    # ------------------------------------------------------------------
    # Direct 'r' key (no need to open the menu)
    # ------------------------------------------------------------------
    BINDINGS = [("r", "rotate", "Rotate Status")]

    def action_rotate(self) -> None:
        self._rotate_status()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    SimpleTUI().run()