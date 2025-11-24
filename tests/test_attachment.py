import pytest
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict
from pydantic import ValidationError
import re
from importlib import import_module, reload


# Mock Dynaconf and load_config for isolation
class MockDynaconf:
    def __init__(self, data: Dict):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)

def mock_load_config(namespace, quiet=True):
    return MockDynaconf({"status_icons": {"success": "👍", "unknown": "ignored"}})

# Patch import in CommandStatus
@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    monkeypatch.setattr("vibedir.config.load_config", mock_load_config)
    # Reload the command_status module to apply the patch to the global instance
    command_status_module = import_module("vibedir.models.command_status")
    reload(command_status_module)

    # CRITICAL: Also reload command_attachment so it picks up the new command_status instance
    command_attachment_module = import_module("vibedir.models.command_attachment")
    reload(command_attachment_module)

# Import classes after mocks (assume fixed code)
from vibedir.models.attachment import Attachment, FileAttachment
from vibedir.models.command_status import CommandStatus, command_status
from vibedir.models.command_attachment import CommandAttachment

logging.getLogger('vibedir').setLevel(logging.DEBUG)
logging.getLogger('vibedir.models').setLevel(logging.DEBUG)

@pytest.fixture
def temp_dir():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        yield Path(tmp)

class TestAttachment:
    def test_creation_valid(self, temp_dir):
        path = temp_dir / "test.txt"
        path.write_text("content")
        att = Attachment(type="file", path=path)
        assert att.type == "file"
        assert isinstance(att.timestamp, datetime)
        assert att.path == path.resolve()
        with pytest.raises(ValidationError):
            att.type = "invalid"

    def test_path_non_existent_warning(self, caplog, temp_dir):
        caplog.set_level(logging.WARNING)
        path = temp_dir / "missing.txt"
        att = Attachment(type="command", path=path)
        assert "Path does not exist" in caplog.text
        assert att.path == path.resolve()

class TestFileAttachment:
    def test_creation_with_hash(self):
        fa = FileAttachment(path=Path("dummy"), original_path=Path("orig"), hash="abc123def")
        assert fa.hash == "abc123def"
        assert fa.original_path == Path("orig")

class TestCommandStatus:
    def test_valid_statuses(self):
        valid = CommandStatus.valid_statuses()
        assert "success" in valid
        assert len(valid) == 6

    def test_get_icon_default_and_override(self):
        status = CommandStatus()
        assert status.get_icon("success") == "👍"
        assert status.get_icon("failed") == "❌"
        with pytest.raises(ValueError):
            status.get_icon("invalid")

    def test_unknown_override_warning(self, caplog):
        caplog.set_level(logging.WARNING)
        _ = CommandStatus()
        assert "Unknown status 'unknown'" in caplog.text

class TestCommandAttachment:
    def test_creation_valid(self, temp_dir):
        path = temp_dir / "test.json"
        path.write_text("{}")
        ca = CommandAttachment(
            name="TestCmd",
            status="success",
            path=path,
            output="output text",
            output_format="log",
        )
        assert ca.name == "TestCmd"
        assert ca.status == "success"
        assert ca.compute_output_path() == path.with_name("test_output.log")
        assert ca.get_status_icon() == "👍"

    def test_status_validation_invalid(self):
        with pytest.raises(ValidationError, match="Invalid status"):
            CommandAttachment(name="Test", status="invalid", path=Path("dummy.json"))

    def test_output_format_validation(self):
        # Valid
        ca = CommandAttachment(name="Test", status="running", path=Path("dummy.json"), output_format="csv-report.long")
        assert ca.output_format == "csv-report.long"

        # Invalid chars
        with pytest.raises(ValidationError, match="Invalid output_format"):
            CommandAttachment(name="Test", status="success", path=Path("dummy.json"), output_format="bad/")

        # Invalid length
        with pytest.raises(ValidationError, match="Invalid output_format length"):
            CommandAttachment(name="Test", status="success", path=Path("dummy.json"), output_format="a" * 41)

    def test_compute_output_path_invalid(self):
        ca = CommandAttachment(name="Test", status="failed", path=Path("not_json.txt"))
        with pytest.raises(ValueError, match="Invalid base path"):
            ca.compute_output_path()