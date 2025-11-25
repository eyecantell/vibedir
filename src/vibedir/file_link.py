from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable
import os
import subprocess

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button
from textual.message import Message


class FileLink(Widget):
    """Clickable filename that opens the real file using a configurable command."""

    DEFAULT_CSS = """
    FileLink {
        layout: horizontal;
        height: auto;
        margin: 0 1;
    }
    FileLink > Button {
        background: transparent;
        color: $primary;
        text-style: underline;
        padding: 0 0;
        border: none;
        width: auto;
    }
    FileLink > Button:hover {
        text-style: bold underline;
    }
    """

    # Class-level default command builder
    # Can be overridden at class or instance level
    default_command_builder: Optional[Callable] = None

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
        command_builder: Optional[Callable] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        path : Path | str
            Full path to the file.
        line, column : int | None
            Optional cursor position to jump to.
        command_builder : Callable | None
            Function that takes (path, line, column) and returns a list of command arguments.
            If None, uses the class-level default_command_builder.
            If that's also None, uses VSCode's 'code --goto' command.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._path = Path(path).resolve()
        self._line = line
        self._column = column
        self._command_builder = command_builder

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
    # Default command builders
    # ------------------------------------------------------------------ #
    @staticmethod
    def vscode_command(path: Path, line: Optional[int], column: Optional[int]) -> list[str]:
        """Build VSCode 'code --goto' command."""
        # Try to get relative path from current working directory
        try:
            cwd = Path.cwd()
            relative_path = path.relative_to(cwd)
            file_arg = str(relative_path)
        except ValueError:
            file_arg = str(path)

        # Build the --goto argument with line:column if provided
        if line is not None:
            goto_arg = f"{file_arg}:{line}"
            if column is not None:
                goto_arg += f":{column}"
        else:
            goto_arg = file_arg

        return ["code", "--goto", goto_arg]

    @staticmethod
    def vim_command(path: Path, line: Optional[int], column: Optional[int]) -> list[str]:
        """Build vim command."""
        cmd = ["vim"]
        if line is not None:
            if column is not None:
                cmd.append(f"+call cursor({line},{column})")
            else:
                cmd.append(f"+{line}")
        cmd.append(str(path))
        return cmd

    @staticmethod
    def nano_command(path: Path, line: Optional[int], column: Optional[int]) -> list[str]:
        """Build nano command."""
        cmd = ["nano"]
        if line is not None:
            if column is not None:
                cmd.append(f"+{line},{column}")
            else:
                cmd.append(f"+{line}")
        cmd.append(str(path))
        return cmd

    @staticmethod
    def eclipse_command(path: Path, line: Optional[int], column: Optional[int]) -> list[str]:
        """Build Eclipse command."""
        cmd = ["eclipse"]
        if line is not None:
            # Eclipse uses --launcher.openFile path:line format
            cmd.extend(["--launcher.openFile", f"{path}:{line}"])
        else:
            cmd.extend(["--launcher.openFile", str(path)])
        return cmd

    @staticmethod
    def copy_path_command(path: Path, line: Optional[int], column: Optional[int]) -> list[str]:
        """Copy the full path (with line:column) to clipboard.
        
        Uses platform-appropriate clipboard commands:
        - Linux: xclip or xsel
        - macOS: pbcopy
        - Windows: clip
        """
        import platform
        
        # Build the path string with line:column
        path_str = str(path)
        if line is not None:
            path_str += f":{line}"
            if column is not None:
                path_str += f":{column}"
        
        # Determine clipboard command based on platform
        system = platform.system()
        if system == "Darwin":  # macOS
            return ["bash", "-c", f"echo -n '{path_str}' | pbcopy"]
        elif system == "Windows":
            return ["cmd", "/c", f"echo {path_str} | clip"]
        else:  # Linux/Unix
            # Try xclip first, fall back to xsel
            return ["bash", "-c", f"echo -n '{path_str}' | xclip -selection clipboard 2>/dev/null || echo -n '{path_str}' | xsel --clipboard"]

    # ------------------------------------------------------------------ #
    # Click handling
    # ------------------------------------------------------------------ #
    @on(Button.Pressed, "#btn")
    async def _on_button_pressed(self, _: Button.Pressed) -> None:
        """Open the file using the configured command."""
        self.post_message(self.Clicked(self._path, self._line, self._column))

        # Determine which command builder to use
        command_builder = (
            self._command_builder 
            or self.default_command_builder 
            or self.vscode_command
        )

        try:
            # Build the command
            cmd = command_builder(self._path, self._line, self._column)
            
            # Execute the command
            result = subprocess.run(
                cmd,
                env=os.environ.copy(),
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.app.notify(f"Opened {self._path.name}", title="FileLink", timeout=1.5)
            else:
                error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
                self.app.notify(
                    f"Failed to open {self._path.name}: {error_msg}",
                    severity="error",
                    timeout=3,
                )
            
        except subprocess.TimeoutExpired:
            self.app.notify(
                f"Timeout opening {self._path.name}",
                severity="error",
                timeout=3,
            )
        except Exception as exc:
            self.app.notify(
                f"Failed to open {self._path.name}: {exc}",
                severity="error",
                timeout=3,
            )