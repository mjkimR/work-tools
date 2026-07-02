import os
import sys

from loguru import logger
from work_tools.core.util.project_path import get_git_repo_root


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def setup_logger(log_path: str | None = None):
    """Setup the logger with console handler and optional file logging."""
    # Remove default handler
    logger.remove()

    # 1. Console (Text + Color)
    logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=False,
        backtrace=False,
        diagnose=False,
    )

    if log_path is None and _env_truthy("WT_FILE_LOG"):
        log_path = os.getenv("WT_LOG_PATH") or f"{get_git_repo_root()}/logs/cli.log"

    if log_path is None:
        return logger

    common_file_config = {
        "sink": log_path,
        "level": "INFO",
        "rotation": "1 day",
        "retention": "30 days",
        "compression": "zip",
        "diagnose": False,
    }

    # 2. File (Text)
    logger.add(
        **common_file_config,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
        backtrace=True,
    )
    return logger
