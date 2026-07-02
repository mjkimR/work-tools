from unittest.mock import patch

import pytest
from work_tools.core.util.project_path import get_git_repo_root


def test_get_git_repo_root_no_git(tmp_path):
    """Test that RuntimeError is raised when no .git directory is found."""
    with (
        patch("pathlib.Path.cwd", return_value=tmp_path),
        patch("work_tools.core.util.project_path._find_project_root_from_file", return_value=None),
    ):
        with pytest.raises(RuntimeError, match="Cannot determine git repository root"):
            get_git_repo_root()


def test_get_git_repo_root_success(tmp_path):
    """Test that the git repository root is correctly found."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        assert get_git_repo_root() == str(tmp_path)


def test_get_git_repo_root_from_subdir(tmp_path):
    """Test that the git repository root is found when called from a subdirectory."""
    git_root = tmp_path / "repo"
    git_root.mkdir()
    (git_root / ".git").mkdir()
    subdir = git_root / "a" / "b" / "c"
    subdir.mkdir(parents=True)

    with patch("pathlib.Path.cwd", return_value=subdir):
        assert get_git_repo_root() == str(git_root)
