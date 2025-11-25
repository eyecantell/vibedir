# demo_file_link.py
from textual.app import App, ComposeResult, on
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.containers import Horizontal, Vertical
from pathlib import Path
from vibedir import FileLink, ToggleableFileLink 


class DemoApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    Horizontal {
        height: auto;
        width: 100%;
    }
    Vertical {
        width: 1fr;
    }
    Label {
        height: 1;
        content-align: center middle;
    }
    ListView {
        height: auto;
        overflow-y: auto;
    }
    ListItem {
        height: 1;
        align: left middle;
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
        
        with Horizontal():
            with Vertical():
                yield Label("Both")
                self.lv1 = ListView()
                yield self.lv1
            with Vertical():
                yield Label(" ")
            with Vertical():
                yield Label("Remove Only")
                self.lv2 = ListView()
                yield self.lv2
            with Vertical():
                yield Label(" ")
            with Vertical():
                yield Label("Toggle Only")
                self.lv3 = ListView()
                yield self.lv3
            with Vertical():
                yield Label(" ")
            with Vertical():
                yield Label("Neither")
                self.lv4 = ListView()
                yield self.lv4
        
        yield Footer()


    @on(FileLink.Clicked)
    def file_clicked(self, event: FileLink.Clicked) -> None:
        pos = f" @ {event.line}:{event.column}" if event.line else ""
        self.log(f"FileLink clicked → {event.path}{pos}")

    def on_mount(self) -> None:
        self.lvs = [self.lv1, self.lv2, self.lv3, self.lv4]
        
        configs = [
            {"show_toggle": True, "show_remove": True},
            {"show_toggle": False, "show_remove": True},
            {"show_toggle": True, "show_remove": False},
            {"show_toggle": False, "show_remove": False},
        ]
        
        for lv in self.lvs:
            lv.can_focus_children = True
        
        for i, lv in enumerate(self.lvs):
            config = configs[i]
            for f in self.FILES:
                list_item = ListItem(
                    ToggleableFileLink(
                        f,
                        line=1,
                        initial_toggle=False,
                        disable_on_untoggle=True,
                        **config
                    ),
                    name=str(f),
                )
                list_item.can_focus_children = True
                lv.append(list_item)

    @on(ToggleableFileLink.Toggled)
    def toggle_handled(self, event: ToggleableFileLink.Toggled) -> None:
        self.log(f"Toggled {event.path} to {event.is_toggled}")

    @on(ToggleableFileLink.Removed)
    def remove_handled(self, event: ToggleableFileLink.Removed) -> None:
        self.log(f"Removed {event.path}")
        # Safely remove by matching ListItem name to str(path)
        path_str = str(event.path)
        for lv in self.lvs:
            for child in list(lv.children):  # Copy list to avoid modification issues
                if isinstance(child, ListItem) and child.name == path_str:
                    child.remove()
                    break

if __name__ == "__main__":
    DemoApp().run()