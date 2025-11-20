from textual import on, work
from textual.message import Message
from textual.widgets import Markdown, Static, TextArea, Button
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.app import ComposeResult
from textual.scroll_view import ScrollView
import time  # For debounce
from .config import load_config

# Load config
CONFIG = load_config("vibedir", config_path=None, quiet=True)
USER_ICON = CONFIG["prompt_icons"]["user"]
ASSISTANT_ICON = CONFIG["prompt_icons"]["assistant"]


class VibedirChatWidget(Widget):
    """TUI widget for displaying/editing prompt.md in a column."""

    class VibedirMessageSubmitted(Message):
        def __init__(self, message: str) -> None:
            super().__init__()
            self.message = message

    DEFAULT_CSS = """
    VibedirChatWidget {
        layout: vertical;
        height: 100%;
        width: 100%;  /* Fits column */
    }
    VibedirChatWidget > ScrollView {
        height: 1fr;
    }
    VibedirChatWidget TextArea {
        width: 1fr;
        height: auto;
        min-height: 3;
        max-height: 10;
        border-top: solid $primary;
    }
    .bubble { padding: 1 3; border: round $primary; border-radius: 16; max-width: 80%; margin: 1 2; }
    .bubble.assistant { background: $surface; color: $text; }
    .bubble.user { background: $accent; }
    .avatar { width: 7; content-align: center middle; padding: 0 1; }
    .message-line { width: 100%; height: auto; padding: 0 1; }
    .remove-btn { margin: 0 1; height: 1; }
    """

    pending_text: reactive[str] = reactive("", recompose=True)
    debounce_timer: Optional[Timer] = None
    history: List[VibedirMessage] = []

    def __init__(self, parser: VibedirPromptParser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser

    def compose(self) -> ComposeResult:
        with ScrollView(id="chat-scroll"):
            yield Vertical(id="chat-messages")
        yield TextArea(placeholder="Edit pending prompt (Ctrl+Enter to submit)...", id="pending-input")

    def on_mount(self) -> None:
        self.load_from_file()

    def load_from_file(self) -> None:
        self.history, pending = self.parser.parse()
        chat_messages = self.query_one("#chat-messages", Vertical)
        chat_messages.clear()
        for idx, msg in enumerate(self.history):
            self._add_bubble(msg.role, msg.content, idx)
        self.pending_text = pending.content if pending else ""
        self.query_one(TextArea).load_text(self.pending_text)
        self.query_one("#chat-scroll", ScrollView).scroll_end()

    def _add_bubble(self, role: str, text: str, idx: int) -> None:
        bubble = Markdown(text)
        bubble.add_class("bubble")
        bubble.add_class("assistant" if role == "assistant" else "user")
        remove_btn = Button("❌ Remove", variant="error", classes="remove-btn")
        remove_btn.add_listener("click", lambda e: self._remove_message(idx))
        line = Horizontal(classes="message-line")
        if role == "assistant":
            line.mount(Static(ASSISTANT_ICON, classes="avatar"))
            line.mount(bubble)
            line.mount(remove_btn)
            line.mount(Static(expand=True))
        else:
            line.mount(Static(expand=True))
            line.mount(bubble)
            line.mount(remove_btn)
            line.mount(Static(USER_ICON, classes="avatar"))
        self.query_one("#chat-messages", Vertical).mount(line)

    def _remove_message(self, idx: int) -> None:
        self.parser.remove_message(idx)
        self.load_from_file()

    @on(TextArea.Changed, "#pending-input")
    def _debounce_write(self, event: TextArea.Changed) -> None:
        if self.debounce_timer:
            self.debounce_timer.stop()
        self.debounce_timer = self.set_timer(0.5, self._write_pending)  # 500ms debounce

    def _write_pending(self) -> None:
        text = self.query_one(TextArea).text.strip()
        self.parser.write_pending(text)
        self.debounce_timer = None

    @on(TextArea.Submitted, "#pending-input")
    def _handle_submit(self, event: TextArea.Submitted) -> None:
        message = event.text.strip()
        if not message:
            return
        self.parser.append_message("user", message)
        self.load_from_file()  # Reload to show new user bubble + empty pending
        self.post_message(self.VibedirMessageSubmitted(message))  # For LLM trigger
