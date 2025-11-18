#!/usr/bin/env python3
"""
vibedir – Textual TUI with configurable commands, icons, and live header
"""

import asyncio
import pathlib
import subprocess
from typing import Dict, List, Any

import tomli  # pip install tomli
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, ListView, ListItem


# ----------------------------------------------------------------------
# 1. Status enum & default icons
# ----------------------------------------------------------------------
class Status:
    NOT_CFG = "not_configured"
    NOT_RUN = "not_run"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


DEFAULT_ICONS: Dict[str, str] = {
    Status.NOT_CFG: "⊘",
    Status.NOT_RUN: "❓",
    Status.RUNNING: "⏳",
    Status.SUCCESS: "✅",
    Status.FAILED: "❌",
}


# ----------------------------------------------------------------------
# 2. Command model
# ----------------------------------------------------------------------
class Command:
    def __init__(self, name: str, cfg: Dict[str, Any]):
        self.name = name
        self.show_in_header = cfg.get("show_in_header", False)
        self.run_on = set(cfg.get("run_on", []))
        self.include_results = cfg.get("include_results", False)
        self.command = cfg.get("command", "")
        self.success = cfg.get("success", "exit_code")
        self.hotkey = cfg.get("hotkey")

        # Plain str – no reactive needed here
        self.status = Status.NOT_CFG if not self.command else Status.NOT_RUN


# ----------------------------------------------------------------------
# 3. Load config.toml (root first, then .vibedir/)
# ----------------------------------------------------------------------
ROOT_CFG = pathlib.Path("config.toml")
SUBDIR_CFG = pathlib.Path(".vibedir/config.toml")


def load_config() -> Dict[str, Any]:
    cfg = {"commands": [], "status_icons": DEFAULT_ICONS.copy()}
    for path in (ROOT_CFG, SUBDIR_CFG):
        if path.exists():
            try:
                with path.open("rb") as f:
                    raw = tomli.load(f)

                # ---- icons ----
                mapping = {
                    "not_configured": Status.NOT_CFG,
                    "not_run": Status.NOT_RUN,
                    "running": Status.RUNNING,
                    "success": Status.SUCCESS,
                    "failed": Status.FAILED,
                }
                for key, internal in mapping.items():
                    if key in raw.get("status_icons", {}):
                        cfg["status_icons"][internal] = raw["status_icons"][key]

                # ---- commands ----
                for cmd_cfg in raw.get("command", []):
                    cfg["commands"].append(Command(cmd_cfg["name"], cmd_cfg))
                break
            except Exception as exc:
                print(f"[vibedir] warning: failed to load {path}: {exc}")
    return cfg


CONFIG = load_config()
ICONS = CONFIG["status_icons"]
COMMANDS: List[Command] = CONFIG["commands"]


# ----------------------------------------------------------------------
# 4. TUI
# ----------------------------------------------------------------------
class SimpleTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #status { height: 3; background: $primary; color: $text; padding: 1; }
    #menu   { height: 1fr; }
    """

    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(id="status")  # will be filled later
        yield ListView(id="menu")
        yield Footer()

    async def on_mount(self) -> None:
        # ---- populate menu ----
        menu = self.query_one("#menu", ListView)
        for cmd in COMMANDS:
            if "no_manual" not in cmd.run_on:
                item_id = f"run_{cmd.name.replace(' ', '_')}"
                await menu.mount(ListItem(Label(f" Run {cmd.name}"), id=item_id))

        # ---- hot-keys ----
        for cmd in COMMANDS:
            if cmd.hotkey:
                action = f"run_{cmd.name.replace(' ', '_')}"
                self.bind(cmd.hotkey, action, description=f"Run {cmd.name}")

        # ---- first header render ----
        self._refresh_status()

    # ------------------------------------------------------------------
    def _render_status(self) -> str:
        parts = [f"{cmd.name}{ICONS[cmd.status]}" for cmd in COMMANDS if cmd.show_in_header]
        return " | ".join(parts) if parts else "No header commands configured"

    def _refresh_status(self) -> None:
        self.query_one("#status", Label).update(self._render_status())

    # ------------------------------------------------------------------
    async def _run_command(self, cmd: Command) -> None:
        if not cmd.command:
            return
        cmd.status = Status.RUNNING
        self._refresh_status()

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd.command.replace("{{ base_directory }}", str(pathlib.Path.cwd())),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            cmd.status = Status.SUCCESS if proc.returncode == 0 else Status.FAILED
        except Exception:
            cmd.status = Status.FAILED
        self._refresh_status()

    # ------------------------------------------------------------------
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        cmd_name = event.item.id.replace("run_", "").replace("_", " ")
        for cmd in COMMANDS:
            if cmd.name == cmd_name:
                asyncio.create_task(self._run_command(cmd))
                self.query_one("#menu", ListView).index = None
                break

    # ------------------------------------------------------------------
    # Dynamic hot-key actions
    # ------------------------------------------------------------------
    def action_run_Format_Code(self) -> None:
        self._run_by_name("Format Code")

    def action_run_Lint(self) -> None:
        self._run_by_name("Lint")

    def action_run_Tests(self) -> None:
        self._run_by_name("Tests")

    def _run_by_name(self, name: str) -> None:
        for cmd in COMMANDS:
            if cmd.name == name:
                asyncio.create_task(self._run_command(cmd))
                break


# ----------------------------------------------------------------------
if __name__ == "__main__":
    SimpleTUI().run()
