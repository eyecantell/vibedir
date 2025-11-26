# demo_file_link_improved.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual import on

from vibedir import FileLink, ToggleableFileLink


@dataclass
class FileStatus:
    """Holds file metadata and state."""
    name: str
    path: Path
    toggled: bool = False
    removed: bool = False
    
    def get_master_link(self) -> ToggleableFileLink:
        """Get a FileLink for the Master column (toggle-only)."""
        return ToggleableFileLink(
            self.path,
            initial_toggle=self.toggled,
            show_toggle=True,
            show_remove=False,
            disable_on_untoggle=False,
        )
    
    def get_selected_link(self) -> ToggleableFileLink:
        """Get a FileLink for the Selected column (toggle + remove)."""
        return ToggleableFileLink(
            self.path,
            initial_toggle=True,
            show_toggle=True,
            show_remove=True,
            disable_on_untoggle=False,
        )
    
    def get_unselected_link(self) -> ToggleableFileLink:
        """Get a FileLink for the Unselected column (remove-only)."""
        return ToggleableFileLink(
            self.path,
            initial_toggle=False,
            show_toggle=False,
            show_remove=True,
            disable_on_untoggle=False,
        )
    
    def get_removed_link(self) -> ToggleableFileLink:
        """Get a FileLink for the Removed column (no controls)."""
        return ToggleableFileLink(
            self.path,
            initial_toggle=False,
            show_toggle=False,
            show_remove=False,
            disable_on_untoggle=False,
        )


class ColumnContainer(Vertical):
    """A labeled column with a scrollable list of file links."""
    
    DEFAULT_CSS = """
    ColumnContainer {
        width: 1fr;
        height: 100%;
        border: solid $primary;
    }
    
    ColumnContainer > Label {
        dock: top;
        width: 100%;
        height: 3;
        content-align: center middle;
        background: $primary;
        color: $text;
        text-style: bold;
    }
    
    ColumnContainer > ScrollableContainer {
        width: 100%;
        height: 1fr;
        padding: 1;
    }
    """
    
    def __init__(self, title: str, name: Optional[str] = None, id: Optional[str] = None):
        super().__init__(name=name, id=id)
        self.title = title
        self.container: Optional[ScrollableContainer] = None
    
    def compose(self) -> ComposeResult:
        yield Label(self.title)
        self.container = ScrollableContainer()
        yield self.container
    
    def clear(self) -> None:
        """Remove all file links from this column."""
        if self.container:
            for child in list(self.container.children):
                child.remove()


class DemoApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #main-container {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.file_statuses: dict[Path, FileStatus] = {}
        self.master_column: Optional[ColumnContainer] = None
        self.selected_column: Optional[ColumnContainer] = None
        self.unselected_column: Optional[ColumnContainer] = None
        self.removed_column: Optional[ColumnContainer] = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(id="main-container"):
            self.master_column = ColumnContainer("Master", id="master")
            yield self.master_column
            
            self.selected_column = ColumnContainer("Selected", id="selected")
            yield self.selected_column
            
            self.unselected_column = ColumnContainer("Unselected", id="unselected")
            yield self.unselected_column
            
            self.removed_column = ColumnContainer("Removed", id="removed")
            yield self.removed_column
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the file list from ./sample_files directory."""
        sample_dir = Path("./sample_files")
        
        if not sample_dir.exists():
            self.notify(
                "Warning: ./sample_files directory not found. Using current directory.",
                severity="warning",
                timeout=5
            )
            sample_dir = Path(".")
        
        # Collect all files (not directories) from sample_files
        files = []
        if sample_dir.exists():
            for item in sample_dir.iterdir():
                if item.is_file():
                    files.append(item)
        
        # Sort alphabetically by name
        files.sort(key=lambda p: p.name.lower())
        
        # Create FileStatus instances
        for file_path in files:
            file_status = FileStatus(
                name=file_path.name,
                path=file_path.resolve(),
                toggled=False,
                removed=False
            )
            self.file_statuses[file_path.resolve()] = file_status
        
        # Populate all columns
        self.refresh_all_columns()
        
        if not files:
            self.notify(
                "No files found in ./sample_files directory",
                severity="warning",
                timeout=5
            )
    
    def refresh_all_columns(self) -> None:
        """Regenerate all columns based on current FileStatus state."""
        self.refresh_master_column()
        self.refresh_selected_column()
        self.refresh_unselected_column()
        self.refresh_removed_column()
    
    def refresh_master_column(self) -> None:
        """Regenerate the Master column."""
        if not self.master_column:
            return
        
        self.master_column.clear()
        
        # Add all files, sorted alphabetically
        for file_status in sorted(self.file_statuses.values(), key=lambda fs: fs.name.lower()):
            link = file_status.get_master_link()
            self.master_column.container.mount(link)
    
    def refresh_selected_column(self) -> None:
        """Regenerate the Selected column."""
        if not self.selected_column:
            return
        
        self.selected_column.clear()
        
        # Add toggled, non-removed files
        for file_status in sorted(self.file_statuses.values(), key=lambda fs: fs.name.lower()):
            if file_status.toggled and not file_status.removed:
                link = file_status.get_selected_link()
                self.selected_column.container.mount(link)
    
    def refresh_unselected_column(self) -> None:
        """Regenerate the Unselected column."""
        if not self.unselected_column:
            return
        
        self.unselected_column.clear()
        
        # Add untoggled, non-removed files
        for file_status in sorted(self.file_statuses.values(), key=lambda fs: fs.name.lower()):
            if not file_status.toggled and not file_status.removed:
                link = file_status.get_unselected_link()
                self.unselected_column.container.mount(link)
    
    def refresh_removed_column(self) -> None:
        """Regenerate the Removed column."""
        if not self.removed_column:
            return
        
        self.removed_column.clear()
        
        # Add removed files
        for file_status in sorted(self.file_statuses.values(), key=lambda fs: fs.name.lower()):
            if file_status.removed:
                link = file_status.get_removed_link()
                self.removed_column.container.mount(link)
    
    @on(ToggleableFileLink.Toggled)
    def handle_toggle(self, event: ToggleableFileLink.Toggled) -> None:
        """Handle toggle state changes."""
        path = event.path
        is_toggled = event.is_toggled
        
        # Update FileStatus
        if path in self.file_statuses:
            file_status = self.file_statuses[path]
            file_status.toggled = is_toggled
            
            # If toggled on and currently removed, unremove it
            if is_toggled and file_status.removed:
                file_status.removed = False
            
            # Refresh all columns to reflect new state
            self.refresh_all_columns()
            
            self.log(f"Toggled {path.name} to {is_toggled}")
    
    @on(ToggleableFileLink.Removed)
    def handle_remove(self, event: ToggleableFileLink.Removed) -> None:
        """Handle remove button clicks."""
        path = event.path
        
        # Update FileStatus
        if path in self.file_statuses:
            file_status = self.file_statuses[path]
            file_status.removed = True
            
            # Refresh all columns to reflect new state
            self.refresh_all_columns()
            
            self.log(f"Removed {path.name}")
    
    @on(FileLink.Clicked)
    def handle_file_click(self, event: FileLink.Clicked) -> None:
        """Handle file link clicks."""
        pos = f" @ {event.line}:{event.column}" if event.line else ""
        self.log(f"FileLink clicked → {event.path.name}{pos}")


if __name__ == "__main__":
    DemoApp().run()