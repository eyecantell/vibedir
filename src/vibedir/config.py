# vibedir/config.py
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import tomlkit  # pip install tomlkit
from dynaconf import Dynaconf
from importlib import resources

__version__ = "0.0.0"

try:
    from importlib.metadata import version

    __version__ = version(__name__.split(".", 1)[0])
except Exception as e:
    logging.getLogger(__name__).debug(f"Failed to load package version: {e}")

logger = logging.getLogger(__name__)
logging.getLogger("vibedir").setLevel(logging.DEBUG)


def check_namespace_value(namespace: str) -> None:
    """Validate that the namespace is a valid Python identifier."""
    if not namespace:
        raise ValueError("Invalid namespace '': must be non-empty")
    if not namespace.isidentifier():
        raise ValueError(f"Invalid namespace '{namespace}': must be a valid Python identifier")


def is_resource(namespace: str, resource_name: str) -> bool:
    """Check if a resource (e.g. bundled config.toml) exists in the package."""
    try:
        return resources.files(namespace).joinpath(resource_name).is_file()
    except (TypeError, FileNotFoundError, AttributeError):
        return False


def home_and_local_config_path(namespace: str) -> Tuple[Path, Path]:
    """Return the expected home and local config file paths."""
    check_namespace_value(namespace)
    home_path = Path.home() / f".{namespace}" / "config.toml"
    local_path = Path.cwd() / f".{namespace}" / "config.toml"
    return home_path, local_path


def get_bundled_config(namespace: str) -> str:
    """Read the bundled default config.toml from the package."""
    if not is_resource(namespace, "config.toml"):
        raise ValueError(f"No bundled config.toml found in package '{namespace}'")
    path = resources.files(namespace) / "config.toml"
    print(f"Loading bundled config from {path}")
    return path.read_text(encoding="utf-8")


def _load_toml_file(path: Path) -> tomlkit.TOMLDocument:
    """Safely load a TOML file with tomlkit (preserves formatting/comments)."""
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return tomlkit.load(f)


def load_config(
    namespace: str,
    config_path: Optional[str] = None,
    quiet: bool = False,
) -> Dynaconf:
    check_namespace_value(namespace)
    settings_files: list[Path] = []

    skip_file_load = os.environ.get("VIBEDIR_SKIP_CONFIG_FILE_LOAD", "false").lower() == "true"
    skip_bundled = os.environ.get("VIBEDIR_SKIP_BUNDLED_CONFIG_LOAD", "false").lower() == "true"

    if config_path:
        cfg_path = Path(config_path).resolve()
        if not cfg_path.is_file():
            raise ValueError(f"Custom config path does not exist: {cfg_path}")
        settings_files.append(cfg_path)
        logger.info(f"Using custom config: {cfg_path}")
        if not quiet:
            print(f"Using custom config: {cfg_path}")

    elif not skip_file_load:
        home_path, local_path = home_and_local_config_path(namespace)
        for p in (home_path, local_path):
            if p.is_file():
                settings_files.append(p)
                logger.info(f"Found config: {p}")
                if not quiet:
                    print(f"Found config: {p}")

    # ---- Bundled fallback -------------------------------------------------
    temp_path: Optional[Path] = None
    if not settings_files and not skip_bundled:
        try:
            content = get_bundled_config(namespace)
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=f"_{namespace}_bundled.toml", delete=False, encoding="utf-8"
            )
            tmp.write(content)
            tmp.close()
            temp_path = Path(tmp.name)
            settings_files.append(temp_path)

            logger.info("Using bundled default config")
            if not quiet:
                print("Using bundled default config")
        except Exception as exc:
            logger.warning(f"Could not load bundled config: {exc}")

    if not settings_files:
        logger.debug("No config files found – Dynaconf will use empty defaults")

    # Dynaconf creation
    settings = Dynaconf(
        settings_files=[str(p) for p in settings_files],
        merge_enabled=True,
        load_dotenv=False,
        uppercase_read_for_dynaconf=False,
    )

    # Force eager loading before we delete the temp file
    if temp_path:
        settings.to_dict()  # <-- this line fixes the crash

    # Cleanup temp file (now safe)
    if temp_path and temp_path.exists():
        try:
            temp_path.unlink()
            logger.debug(f"Cleaned up temporary bundled config {temp_path}")
        except Exception as exc:
            logger.warning(f"Failed to remove temp config {temp_path}: {exc}")

    return settings


def save_config(
    namespace: str,
    updates: dict,
    target: Optional[str] = None,
    quiet: bool = False,
) -> Path:
    """
    Persist configuration changes back to a TOML file using tomlkit.
    By default writes to the **local** .vibedir/config.toml (creates if missing).

    Args:
        namespace: Usually "vibedir"
        updates: dict of changes, supports dotted keys (e.g. {"llm.model": "grok-4"})
        target: Optional explicit path; if None → local config
        quiet: Suppress console output

    Returns:
        Path to the file that was written
    """
    check_namespace_value(namespace)

    if target:
        config_path = Path(target).expanduser().resolve()
    else:
        _, config_path = home_and_local_config_path(namespace)

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # If file doesn't exist, start from bundled defaults
    if not config_path.is_file():
        content = get_bundled_config(namespace)
        doc = tomlkit.loads(content)
        if not quiet:
            print(f"Created new config file: {config_path}")
    else:
        doc = _load_toml_file(config_path)

    # Apply updates (supports nested dotted notation)
    for key_path, value in updates.items():
        parts = key_path.split(".")
        current = doc
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], tomlkit.container.Container):
                current[part] = tomlkit.table()
            current = current[part]
        current[parts[-1]] = value

    # Write back with nice formatting
    with config_path.open("w", encoding="utf-8") as f:
        tomlkit.dump(doc, f)

    logger.info(f"Config saved to {config_path}")
    if not quiet:
        print(f"Config saved → {config_path}")

    return config_path


def init_config(
    namespace: str,
    config_path: str = "",
    force: bool = False,
    quiet: bool = False,
) -> None:
    """
    Create a fresh config file from the bundled default.
    """
    check_namespace_value(namespace)

    if not config_path:
        _, default_path = home_and_local_config_path(namespace)
    else:
        default_path = Path(config_path)

    if default_path.exists() and not force:
        msg = f"Config file already exists: {default_path}\nUse --force to overwrite."
        logger.error(msg)
        if not quiet:
            print(msg)
        raise SystemExit(1)

    content = get_bundled_config(namespace)
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_text(content, encoding="utf-8")

    logger.info(f"Initialized config at {default_path}")
    if not quiet:
        print(f"Initialized config → {default_path}")