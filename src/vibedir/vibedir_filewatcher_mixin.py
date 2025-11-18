from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from textual.app import on
from textual.message import Message


class VibedirFileWatcherMixin:
    """Mixin for watching prompt.md changes."""

    def __init__(self, parser: VibedirPromptParser, chat_widget_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.chat_widget_id = chat_widget_id
        self.observer = Observer()
        self.event_handler = self._create_handler()

    def _create_handler(self):
        class Handler(FileSystemEventHandler):
            def on_modified(inner_self, event):
                if event.src_path == str(self.parser.file_path):
                    self.app.post_message(VibedirFileChanged())

        return Handler()

    def on_mount(self) -> None:
        self.observer.schedule(self.event_handler, str(self.parser.file_path.parent), recursive=False)
        self.observer.start()

    def on_unmount(self) -> None:
        self.observer.stop()
        self.observer.join()


class VibedirFileChanged(Message):
    pass


# In your App:
@on(VibedirFileChanged)
def handle_file_change(self):
    chat = self.query_one(f"#{self.chat_widget_id}", VibedirChatWidget)
    chat.load_from_file()
