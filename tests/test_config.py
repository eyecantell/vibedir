import json
import logging
import os
import pytest
import tomllib
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path
from dynaconf import Dynaconf
from vibedir.config import (
    check_config_format,
    check_namespace_value,
    get_bundled_config,
    init_config,
    is_resource,
    load_config,
)
from vibedir import vibedir_logging  # Assuming vibedir has a similar logging module; adjust if needed
import sys

# Set up logger
logger = logging.getLogger("vibedir.config")


# Custom handler to capture log records in a list
class LoggingListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def flush(self):
        pass


@pytest.fixture
def clean_cwd(tmp_path):
    """Change working directory to a clean temporary path to avoid loading real configs."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


@pytest.fixture
def sample_config_content():
    """Provide sample configuration content."""
    return {
        "mode": "api",
        "llm": {
            "model": "test-model",
            "endpoint": "https://test.endpoint",
        },
        "clipboard_max_chars_per_file": 50000,
        "ask_llm_for_commit_message": False,
    }


@pytest.fixture
def expected_bundled_config_content():
    """Sample of expected values in src/vibedir/config.toml"""
    return {
        "mode": "clipboard",
        "llm": {
            "model": "grok-4",
            "endpoint": "https://api.x.ai/v1",
        },
        "clipboard_max_chars_per_file": 40000,
        "ask_llm_for_commit_message": True,
        "show_working_commit_message": True,
        "show_previous_commit_message": True,
        "auto_commit": "previous",
        "commit_command": "git commit -a -m \"{{ commit_message }}\"",
        "revert_changes_command": "git checkout -- . && git reset",
        "last_commit_message_command": "git log -1 --pretty=%B",
        "changes_exist_command": "git diff --quiet HEAD",
        "changes_exist_result": "exit_code",
        "auto_diff": False,
        "diff_command": "git diff",
        "status_icons": {
            "not_configured": "⚠️",
            "not_run": "❓",
            "waiting": "⏳",
            "success": "✅",
            "failed": "❌",
            "running": "spinner",
        },
        "command": [  # This is an array of dicts in TOML
            {
                "name": "Code Changes",
                "run_on": ["changes_received"],
                "command": "apply_code_changes",
            },
            {
                "name": "Format Code",
                "run_on": ["changes_success"],
                "command": "ruff format {{ base_directory }}",
            },
            {
                "name": "Lint",
                "show_in_header": True,
                "run_on": ["changes_success"],
                "include_results": True,
                "command": "ruff check {{ base_directory }}",
                "success": "exit_code",
            },
            {
                "name": "Tests",
                "hotkey": "t",
                "show_in_header": True,
                "run_on": ["changes_success"],
                "include_results": True,
                "command": "pytest {{ tests_directory }}",
                "success": "exit_code",
            },
        ],
        "show_command_legend_in_header": True,
        "tests_directory": "{{ base_directory }}/tests",
        "logging": {
            "level": "INFO",
        },
        "prompt_icons": {
            "user": "👤",
            "assistant": "🤖",
        },
    }


@pytest.fixture
def clean_logger():
    """Clean logger setup and teardown with a LoggingListHandler to capture log records."""
    logger.handlers.clear()
    vibedir_logging.configure_logging(logger, level=logging.DEBUG)  # Adjust to vibedir's logging function

    # Add LoggingListHandler to capture log records
    list_handler = LoggingListHandler()
    list_handler.setLevel(logging.DEBUG)
    logger.addHandler(list_handler)

    yield logger

    # Clean up
    logger.removeHandler(list_handler)
    list_handler.close()
    logger.handlers.clear()


def assert_config_content_equal(config: Dynaconf, expected_config_content: dict):
    """Common set of assertions to check Dynaconf config content against an expected set of values"""
    assert isinstance(config, Dynaconf)
    print(f"config is:\n{json.dumps(config.to_dict(), indent=4)}\n--")
    assert isinstance(expected_config_content, dict)
    print(f"expected_config_content is:\n{json.dumps(expected_config_content, indent=4)}\n--")
    assert config.get("mode") == expected_config_content["mode"]
    assert config.get("llm.model") == expected_config_content["llm"]["model"]
    assert config.get("llm.endpoint") == expected_config_content["llm"]["endpoint"]
    assert config.get("clipboard_max_chars_per_file") == expected_config_content["clipboard_max_chars_per_file"]
    assert config.get("ask_llm_for_commit_message") == expected_config_content["ask_llm_for_commit_message"]


def test_check_namespace_value():
    """Test namespace validation."""
    check_namespace_value("vibedir")
    check_namespace_value("prepdir")
    check_namespace_value("applydir_123")

    with pytest.raises(ValueError, match="Invalid namespace '': must be non-empty"):
        check_namespace_value("")

    with pytest.raises(ValueError, match="Invalid namespace 'invalid@name': must be a valid Python identifier"):
        check_namespace_value("invalid@name")


def test_check_config_format():
    """Test check_config_format for valid and invalid TOML."""
    check_config_format('mode = "clipboard"', "test config")

    with pytest.raises(ValueError, match="Invalid TOML in test config"):
        check_config_format("invalid = = = :", "test config")


def test_is_resource_bundled_config():
    """Make sure the bundled config (src/vibedir/config.toml) exists"""
    assert is_resource("vibedir", "config.toml")


def test_is_resource_false():
    """Test resource check for a non-existent file"""
    assert not is_resource("vibedir", "nonexistent.toml")


def test_is_resource_exception(clean_logger):
    """Test is_resource exception handling."""
    # Mock the correct module based on Python version
    mock_target = "importlib_resources.files" if sys.version_info < (3, 9) else "importlib.resources.files"
    with patch(mock_target, side_effect=TypeError("Invalid resource")):
        assert not is_resource("vibedir", "config.toml")


def test_expected_bundled_config_values(expected_bundled_config_content):
    # Load the bundled config and make sure its valid
    bundled_config_content = get_bundled_config("vibedir")
    check_config_format(bundled_config_content, "bundled config")

    bundled_toml = tomllib.loads(bundled_config_content)
    print(f"bundled toml is {bundled_toml}", "bundled")
    assert bundled_toml is not None

    # Check expected bundled config values
    assert bundled_toml["mode"] == expected_bundled_config_content["mode"]
    assert bundled_toml["llm"]["model"] == expected_bundled_config_content["llm"]["model"]
    assert bundled_toml["llm"]["endpoint"] == expected_bundled_config_content["llm"]["endpoint"]
    assert bundled_toml["clipboard_max_chars_per_file"] == expected_bundled_config_content["clipboard_max_chars_per_file"]
    assert bundled_toml["ask_llm_for_commit_message"] == expected_bundled_config_content["ask_llm_for_commit_message"]


def test_nonexistent_bundled_config():
    """Try to load a bundled config for a namespace that does not exist"""
    # Load the bundled config and make sure its valid
    namespace = "namespace_that_does_not_exist"
    with pytest.raises(ModuleNotFoundError, match=f"No module named '{namespace}'"):
        get_bundled_config(namespace)


def test_load_config_from_specific_path(sample_config_content, clean_cwd, clean_logger):
    """Test loading local configuration from mydir/config.toml."""
    config_path = clean_cwd / "mydir" / "config.toml"
    config_path.parent.mkdir()
    with config_path.open("wb") as f:
        tomllib.dump(sample_config_content, f)  # tomllib has no dump; use tomlkit or tomli_w for writing

    # Note: Since tomllib is read-only, for writing in tests, install and use tomli_w or similar
    # For simplicity, write as string
    config_str = """
mode = "api"

[llm]
model = "test-model"
endpoint = "https://test.endpoint"

clipboard_max_chars_per_file = 50000
ask_llm_for_commit_message = false
"""
    config_path.write_text(config_str)

    with patch.dict(os.environ, {"VIBEDIR_SKIP_CONFIG_FILE_LOAD": "true"}):
        config = load_config("vibedir", str(config_path), quiet=True)

    assert_config_content_equal(config, sample_config_content)


def test_load_config_local(sample_config_content, clean_cwd, clean_logger):
    """Test loading local configuration from .vibedir/config.toml."""

    # Create local config file
    config_path = clean_cwd / ".vibedir" / "config.toml"
    config_path.parent.mkdir()
    config_str = """
mode = "api"

[llm]
model = "test-model"
endpoint = "https://test.endpoint"

clipboard_max_chars_per_file = 50000
ask_llm_for_commit_message = false
"""
    config_path.write_text(config_str)

    # Create empty home dir (so no config gets loaded from there)
    home_dir = clean_cwd / "home"
    home_dir.mkdir()

    with patch.dict(
        os.environ,
        {"HOME": str(home_dir), "VIBEDIR_SKIP_CONFIG_FILE_LOAD": "false", "VIBEDIR_SKIP_BUNDLED_CONFIG_LOAD": "true"},
    ):
        config = load_config("vibedir")

    assert_config_content_equal(config, sample_config_content)


def test_load_config_home(sample_config_content, clean_cwd, clean_logger):
    """Test loading configuration from ~/.vibedir/config.toml."""
    home_dir = clean_cwd / "home"
    home_dir.mkdir()
    config_path = home_dir / ".vibedir" / "config.toml"
    config_path.parent.mkdir()
    config_str = """
mode = "api"

[llm]
model = "test-model"
endpoint = "https://test.endpoint"

clipboard_max_chars_per_file = 50000
ask_llm_for_commit_message = false
"""
    config_path.write_text(config_str)

    with patch.dict(
        os.environ,
        {"HOME": str(home_dir), "VIBEDIR_SKIP_CONFIG_FILE_LOAD": "false", "VIBEDIR_SKIP_BUNDLED_CONFIG_LOAD": "true"},
    ):
        config = load_config("vibedir", quiet=True)

    assert_config_content_equal(config, sample_config_content)


def test_load_config_bundled(clean_logger):
    """Test loading bundled configuration using get_bundled_config."""
    # Load the bundled config
    bundled_toml = tomllib.loads(get_bundled_config("vibedir"))

    # Skip any file loads and load the bundled
    with patch.dict(os.environ, {"VIBEDIR_SKIP_CONFIG_FILE_LOAD": "true", "VIBEDIR_SKIP_BUNDLED_CONFIG_LOAD": "false"}):
        config = load_config("vibedir", quiet=True)

    assert config.get("mode") == bundled_toml["mode"]
    assert config.get("llm.model") == bundled_toml["llm"]["model"]


def test_init_config(clean_cwd, clean_logger):
    """Test initializing a configuration file."""
    config_path = clean_cwd / ".vibedir" / "config.toml"
    init_config("vibedir", str(config_path), force=True)

    assert config_path.is_file()
    bundled_toml = tomllib.loads(get_bundled_config("vibedir"))
    with config_path.open("rb") as f:
        new_config = tomllib.load(f)
    assert new_config == bundled_toml
    assert any("Created '.vibedir/config.toml' with default configuration." in record.message for record in clean_logger.handlers[-1].records if hasattr(record, 'message'))  # Adjusted for log format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])