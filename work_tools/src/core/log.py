import sys

from loguru import logger
from util.project_path import get_git_repo_root


def setup_logger(log_path: str | None = None):
    """Setup the logger with console and file handlers"""
    # Remove default handler
    logger.remove()
    if log_path is None:
        log_path = f"{get_git_repo_root()}/logs/cli.log"

    common_file_config = {
        "sink": log_path,
        "level": "INFO",
        "rotation": "1 day",
        "retention": "30 days",
        "compression": "zip",
        "diagnose": False,
    }

    # 1. Console (Text + Color)
    logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=False,
        backtrace=False,
        diagnose=False,
    )
    # 2. File (Text)
    logger.add(
        **common_file_config,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
        backtrace=True,
    )
    return logger
