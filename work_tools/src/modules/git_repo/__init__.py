"""
git_repo
--------
CLI tool for Git repository operations.
Provides context for AI-assisted workflows such as generating commit messages,
retrieving staged diffs, recent commit history, and current branch information.
"""

from .api import cli
from .git_log import GitRepoManager

__all__ = [
    "cli",
    "GitRepoManager",
]
