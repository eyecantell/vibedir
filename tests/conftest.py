import pytest
import logging
import os
from vibedir import __version__


@pytest.fixture(autouse=True)
def reset_loggers():
    """Reset vibedir loggers before each test to avoid interference."""
    for name in ("vibedir", "vibedir.config", "dynaconf"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
    yield


@pytest.fixture(autouse=True, scope="function")
def reset_env():
    """Restore environment variables after each test."""
    keys = ["VIBEDIR_SKIP_CONFIG_FILE_LOAD", "VIBEDIR_SKIP_BUNDLED_CONFIG_LOAD", "HOME"]
    snapshot = {k: os.environ.get(k) for k in keys}

    yield

    for k in keys:
        if snapshot[k] is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = snapshot[k]


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary project directory – useful for future tests."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "src" / "main.py").write_text('print("hello vibedir")\n')
    return project_dir