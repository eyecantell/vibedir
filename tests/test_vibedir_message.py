import pytest
from pathlib import Path
from vibedir import VibedirPromptParser, VibedirMessage 

# Fixture for your real sample file
@pytest.fixture
def sample_parser():
    file_path = Path("tests/sample_prompt.md")
    assert file_path.exists(), "sample_prompt.md not found in tests/"
    return VibedirPromptParser(file_path)

# Fixture for temporary files
@pytest.fixture
def temp_parser(tmp_path):
    file_path = tmp_path / "prompt.md"
    parser = VibedirPromptParser(file_path)
    parser.init_file()
    return parser

def test_parse_sample(sample_parser):
    history, pending = sample_parser.parse()

    assert len(history) == 4

    assert history[0].role == "user"
    assert history[0].timestamp == "2025-11-17 14:22:31.222"
    assert "fastapi" in history[0].content.lower()
    assert "plotly" in history[0].content.lower()

    assert history[1].role == "assistant"
    assert history[1].timestamp == "2025-11-17 14:23:15.312"
    assert "initial implementation" in history[1].content

    assert history[2].role == "user"
    assert history[2].timestamp == "2025-11-17 14:25:10.123"
    assert "jwt" in history[2].content.lower()

    assert history[3].role == "assistant"
    assert history[3].timestamp == "2025-11-17 14:25:48.124"
    assert "updated with jwt auth" in history[3].content.lower()

    assert pending.role == "pending"
    assert "async" in pending.content
    assert "rate limiting" in pending.content
    assert "traceback" in pending.content.lower()

def test_init_file(temp_parser):
    history, pending = temp_parser.parse()
    assert len(history) == 0
    assert pending.content == ""

def test_append_and_parse(temp_parser):
    temp_parser.append_message("user", "Hello world!")
    temp_parser.append_message("assistant", "Hi there!", model="grok-4")

    history, pending = temp_parser.parse()
    assert len(history) == 2
    assert history[0].content == "Hello world!"
    assert history[1].content == "Hi there!"
    assert pending.content == ""

def test_write_pending(temp_parser):
    temp_parser.write_pending("New pending text\nwith lines")
    history, pending = temp_parser.parse()
    assert pending.content == "New pending text\nwith lines"

def test_remove_message(temp_parser):
    temp_parser.append_message("user", "Msg 1")
    temp_parser.append_message("assistant", "Resp 1")
    temp_parser.append_message("user", "Msg 2")

    temp_parser.remove_message(1)  # remove assistant response
    history, _ = temp_parser.parse()
    assert len(history) == 2
    assert history[0].content == "Msg 1"
    assert history[1].content == "Msg 2"

def test_to_markdown_header():
    msg = VibedirMessage("pending", None, "Test pending")
    header = msg.to_markdown_header()
    assert "Pending → (edit below)" in header
    assert "Test pending" in header

    msg = VibedirMessage("user", "2025-11-17 12:00:00.000", "User msg")
    header = msg.to_markdown_header()
    assert "User - 2025-11-17 12:00:00.000" in header