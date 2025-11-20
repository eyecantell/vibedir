# tests/test_config.py
import json
import logging
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

import tomlkit
from dynaconf import Dynaconf

from vibedir.config import (
    load_config,
    init_config,
    save_config,
    get_bundled_config,
    is_resource,
    check_namespace_value,
    home_and_local_config_path,
)

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def clean_cwd(tmp_path):
    original = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


@pytest.fixture
def clean_logger():
    logger = logging.getLogger("vibedir.config")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()  # simple handler for capture
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    yield logger

    logger.handlers.clear()


@pytest.fixture
def bundled_dict():
    """Return the expected bundled config as a Python dict."""
    content = get_bundled_config("vibedir")
    return tomlkit.loads(content).unwrap()  # .unwrap() gives plain dict


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def test_check_namespace_value():
    check_namespace_value("vibedir")
    check_namespace_value("MyApp_123")

    with pytest.raises(ValueError):
        check_namespace_value("")

    with pytest.raises(ValueError):
        check_namespace_value("invalid name")


def test_is_resource_bundled_exists():
    assert is_resource("vibedir", "config.toml") is True


def test_is_resource_missing():
    assert is_resource("vibedir", "missing.toml") is False


def test_get_bundled_config_returns_valid_toml(bundled_dict):
    content = get_bundled_config("vibedir")
    parsed = tomlkit.loads(content)
    parsed_dict = parsed.unwrap()

    assert parsed_dict["mode"] == "clipboard"
    assert parsed_dict["llm"]["model"] == "grok-4"
    assert parsed_dict["clipboard_max_chars_per_file"] == 40000
    assert parsed_dict["ask_llm_for_commit_message"] is True


def test_load_config_custom_path(clean_cwd):
    custom_path = clean_cwd / "myconfig.toml"
    custom_path.write_text(
        """
mode = "api"
clipboard_max_chars_per_file = 99999

[llm]
model = "custom-model"
endpoint = "https://example.com"
"""
    )

    config = load_config("vibedir", config_path=str(custom_path), quiet=True)

    assert config.mode == "api"
    assert config.llm.model == "custom-model"
    assert config.clipboard_max_chars_per_file == 99999


def test_load_config_local_precedence_over_home(clean_cwd):
    # Home config
    home_dir = clean_cwd / "home"
    home_dir.mkdir()
    os.environ["HOME"] = str(home_dir)
    (home_dir / ".vibedir").mkdir()
    (home_dir / ".vibedir" / "config.toml").write_text('mode = "clipboard"')

    # Local config (should win)
    local_path = clean_cwd / ".vibedir" / "config.toml"
    local_path.parent.mkdir()
    local_path.write_text('mode = "api"')

    config = load_config("vibedir", quiet=True)
    assert config.mode == "api"  # local wins


def test_load_config_falls_back_to_bundled(clean_cwd, bundled_dict):
    # No config files anywhere
    os.environ.pop("HOME", None)

    with patch.dict(os.environ, {
        "VIBEDIR_SKIP_CONFIG_FILE_LOAD": "true",
        "VIBEDIR_SKIP_BUNDLED_CONFIG_LOAD": "false"
    }):
        config = load_config("vibedir", quiet=True)

    assert config.mode == bundled_dict["mode"]
    assert config.llm.model == bundled_dict["llm"]["model"]
    assert config.clipboard_max_chars_per_file == bundled_dict["clipboard_max_chars_per_file"]


def test_init_config_creates_file_from_bundled(clean_cwd):
    target = clean_cwd / ".vibedir" / "config.toml"

    init_config("vibedir", config_path=str(target), force=True, quiet=True)

    assert target.is_file()
    written = tomlkit.loads(target.read_text()).unwrap()
    bundled = tomlkit.loads(get_bundled_config("vibedir")).unwrap()
    assert written == bundled


def test_init_config_refuses_to_overwrite_without_force(clean_cwd):
    target = clean_cwd / ".vibedir" / "config.toml"
    target.parent.mkdir()
    target.write_text("mode = 'clipboard'")

    with pytest.raises(SystemExit):
        init_config("vibedir", config_path=str(target), quiet=True)


def test_save_config_creates_local_file_if_missing(clean_cwd, bundled_dict):
    # No config file exists yet
    assert not (clean_cwd / ".vibedir" / "config.toml").exists()

    saved_path = save_config(
        "vibedir",
        updates={"mode": "api", "clipboard_max_chars_per_file": 12345},
        quiet=True,
    )

    assert saved_path == clean_cwd / ".vibedir" / "config.toml"
    assert saved_path.is_file()

    config = load_config("vibedir", quiet=True)
    assert config.mode == "api"
    assert config.clipboard_max_chars_per_file == 12345

    # Bundled values that weren't touched should still be there
    assert config.llm.model == bundled_dict["llm"]["model"]


def test_save_config_preserves_comments_and_formatting(clean_cwd):
    # Start with bundled config (has comments)
    init_config("vibedir", force=True, quiet=True)

    path = clean_cwd / ".vibedir" / "config.toml"
    original_content = path.read_text()
    assert "# The mode determines" in original_content  # assuming your bundled has this comment; adjust if needed

    save_config("vibedir", {"mode": "api"}, quiet=True)

    new_content = path.read_text()
    assert "# The mode determines" in new_content  # comment preserved!
    assert 'mode = "api"' in new_content


def test_save_config_nested_dotted_keys(clean_cwd):
    init_config("vibedir", force=True, quiet=True)

    save_config(
        "vibedir",
        {
            "llm.model": "claude-3",
            "clipboard_max_chars_per_file": 98765,
            "auto_commit": "latest",
        },
        quiet=True,
    )

    config = load_config("vibedir", quiet=True)
    assert config.llm.model == "claude-3"
    assert config.clipboard_max_chars_per_file == 98765
    assert config.auto_commit == "latest"


def test_save_config_to_explicit_path(clean_cwd):
    target = clean_cwd / "custom_dir" / "myconfig.toml"
    save_config("vibedir", {"mode": "api"}, target=str(target), quiet=True)

    assert target.is_file()
    doc = tomlkit.loads(target.read_text())
    assert doc["mode"] == "api"


def test_home_and_local_config_path():
    home, local = home_and_local_config_path("vibedir")
    assert home == Path.home() / ".vibedir" / "config.toml"
    assert str(local).endswith(".vibedir/config.toml")
    assert local.is_absolute()

# Add these tests to tests/test_config.py

def test_config_merging_precedence(clean_cwd, bundled_dict):
    """
    Test full merge chain with correct precedence:
    bundled (lowest) → home → local (highest)
    Local wins > home > bundled
    """
    # 1. Home config (medium precedence)
    home_dir = clean_cwd / "home"
    home_dir.mkdir()
    os.environ["HOME"] = str(home_dir)
    home_config = home_dir / ".vibedir" / "config.toml"
    home_config.parent.mkdir()
    home_config.write_text("""
mode = "clipboard"
clipboard_max_chars_per_file = 30000
llm.model = "grok-beta"
auto_commit = "off"
""")

    # 2. Local config (highest precedence)
    local_config = clean_cwd / ".vibedir" / "config.toml"
    local_config.parent.mkdir()
    local_config.write_text("""
mode = "api"
clipboard_max_chars_per_file = 99999
ask_llm_for_commit_message = false
""")

    # Load config (bundled + home + local)
    config = load_config("vibedir", quiet=True)

    # Local wins
    assert config.mode == "api"
    assert config.clipboard_max_chars_per_file == 99999
    assert config.ask_llm_for_commit_message is False

    # Home wins over bundled
    assert config.llm.model == "grok-beta"
    assert config.auto_commit == "off"

    # Bundled values still present if not overridden
    assert config.show_command_legend_in_header is True
    assert config.prompt_icons.user == "👤"
    assert config.logging.level == "INFO"


def test_config_custom_path_highest_precedence(clean_cwd):
    """Custom path should override everything (local/home/bundled)"""
    custom_path = clean_cwd / "myconfig.toml"
    custom_path.write_text("""
mode = "api"
llm.model = "claude-3"
clipboard_max_chars_per_file = 11111
""")

    # Create conflicting local config
    local_config = clean_cwd / ".vibedir" / "config.toml"
    local_config.parent.mkdir()
    local_config.write_text('mode = "clipboard"\nllm.model = "local-model"')

    config = load_config("vibedir", config_path=str(custom_path), quiet=True)

    # Custom path wins over local
    assert config.mode == "api"
    assert config.llm.model == "claude-3"
    assert config.clipboard_max_chars_per_file == 11111


def test_config_merge_nested_tables_and_arrays(clean_cwd):
    """Verify that array-of-tables (AOT) are appended across files → total grows"""
    # Home config: adds one extra command
    home_dir = clean_cwd / "home"
    home_dir.mkdir()
    os.environ["HOME"] = str(home_dir)

    home_vibedir = home_dir / ".vibedir"
    home_vibedir.mkdir()                                 # ← this was missing!
    (home_vibedir / "config.toml").write_text("""
[[command]]
name = "Custom Build"
command = "make build"
run_on = ["changes_success"]
""")

    # Local config: adds another command
    local_vibedir = clean_cwd / ".vibedir"
    local_vibedir.mkdir()
    (local_vibedir / "config.toml").write_text("""
[[command]]
name = "Deploy"
command = "make deploy"
run_on = ["changes_success"]
""")

    config = load_config("vibedir", quiet=True)

    commands = config.command
    assert len(commands) == 5                     # 3 bundled + 1 home + 1 local

    names = {cmd["name"] for cmd in commands}
    assert names == {
        "Format Code", "Lint", "Tests", "Custom Build", "Deploy"
    }


def test_config_merge_preserves_order_of_array_tables(clean_cwd):
    """Array-of-tables must be appended in file order: bundled → home → local"""
    home_dir = clean_cwd / "home"
    home_dir.mkdir()
    os.environ["HOME"] = str(home_dir)

    # Home config adds a command
    home_vibedir = home_dir / ".vibedir"
    home_vibedir.mkdir()
    (home_vibedir / "config.toml").write_text("""
[[command]]
name = "HOME_FIRST"
command = "echo home"
run_on = ["startup"]
""")

    # Local config adds another
    local_vibedir = clean_cwd / ".vibedir"
    local_vibedir.mkdir()
    (local_vibedir / "config.toml").write_text("""
[[command]]
name = "LOCAL_LAST"
command = "echo local"
run_on = ["startup"]
""")

    config = load_config("vibedir", quiet=True)

    names = [cmd["name"] for cmd in config.command]

    # Find positions of our markers
    home_idx = names.index("HOME_FIRST")
    local_idx = names.index("LOCAL_LAST")

    # Home command must appear before local command → proves correct merge order
    assert home_idx < local_idx

    # Bonus: bundled "Format Code" should be first
    assert names[0] == "Format Code"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])