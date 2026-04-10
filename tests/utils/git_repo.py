"""Helpers for creating temporary git repositories in tests.

Usage in conftest.py::

    from tests.utils.git_repo import make_git_repo

    @pytest.fixture
    def git_manager(tmp_path):
        return make_git_repo(tmp_path)
"""

import subprocess
from pathlib import Path

from modules.git_repo.config import GitRepoSettings
from modules.git_repo.git_log import GitRepoManager

_TEST_EMAIL = "test@example.com"
_TEST_NAME = "Test User"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in the given repo directory."""
    cmd = ["git", "-C", str(repo), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git setup failed: {' '.join(args)}\n{result.stderr.strip()}")
    return result


def make_git_repo(
    tmp_path: Path,
    *,
    user_email: str = _TEST_EMAIL,
    user_name: str = _TEST_NAME,
    initial_commits: list[str] | None = None,
) -> GitRepoManager:
    """Create a real git repo in *tmp_path* and return a ``GitRepoManager`` pointing at it.

    Args:
        tmp_path: Directory to initialise the repo in (use pytest's ``tmp_path``).
        user_email: Author email for commits and GitRepoSettings filter.
        user_name: Author name for commits.
        initial_commits: Optional list of commit messages to create as empty
            commits.  Defaults to three sample commits if *None*.

    Returns:
        A ``GitRepoManager`` configured to operate on the temporary repo.
    """
    # Init repo
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", user_email)
    _git(tmp_path, "config", "user.name", user_name)

    # Seed commits
    messages = (
        initial_commits
        if initial_commits is not None
        else [
            "Initial commit",
            "Add login feature",
            "Fix dashboard bug",
        ]
    )
    for msg in messages:
        _git(tmp_path, "commit", "--allow-empty", "-m", msg)

    settings = GitRepoSettings(
        user_email=user_email,
        path=str(tmp_path),
    )  # type: ignore[call-arg]
    return GitRepoManager(settings=settings)
