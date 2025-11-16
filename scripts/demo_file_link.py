# demo_file_link.py
from textual.app import App, ComposeResult, on
from textual.widgets import Header, Footer, ListView, ListItem
from pathlib import Path
from vibedir import FileLink  # Assuming this is your import path


class DemoApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    """

    # Define files as a class attr for access in on_mount
    FILES = [
        Path("/mounted/dev/vibedir/vibedir.md"),
        Path("/mounted/dev/vibedir/README.md"),
        Path("/mounted/dev/vibedir/src/main.py"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        # Single link (no change)
        yield FileLink("/mounted/dev/vibedir/vibedir.md", line=42)

        # Yield empty ListView first
        self.lv = ListView()
        yield self.lv

    def on_mount(self) -> None:
        # Now populate safely after mounting
        for f in self.FILES:
            self.lv.append(ListItem(FileLink(f, line=1), name=str(f)))

    @on(FileLink.Clicked)
    def file_clicked(self, event: FileLink.Clicked) -> None:
        pos = f" @ {event.line}:{event.column}" if event.line else ""
        self.log(f"FileLink clicked → {event.path}{pos}")


if __name__ == "__main__":
    DemoApp().run()