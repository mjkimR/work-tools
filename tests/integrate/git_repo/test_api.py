"""Integration tests for Git Repo CLI using safe temporary git manager."""

import subprocess

import pytest
from click.testing import CliRunner
from modules.git_repo.api import cli


@pytest.fixture
def runner():
    """Returns a Click CLI Runner."""
    return CliRunner()


@pytest.fixture
def patch_manager(monkeypatch, git_manager):
    """Patch get_manager in api to return the safe temporary git_manager."""
    monkeypatch.setattr("modules.git_repo.api.get_manager", lambda: git_manager)
    return git_manager


class TestGitRepoCLI:
    """Tests the GitRepo API CLI Endpoints."""

    def test_log_command(self, runner, patch_manager):
        """Test the log command fetches basic mock commits."""
        # The temporary repo has 3 mock commits. We use HEAD~2..HEAD
        result = runner.invoke(cli, ["log", "HEAD~2..HEAD"])

        assert result.exit_code == 0
        assert "Repository   :" in result.output
        assert "Found" in result.output
        assert "Add login feature" in result.output  # One of our mocked commits

    def test_commit_info_command_no_staged(self, runner, patch_manager):
        """Test commit-info exits when there are no staged changes."""
        result = runner.invoke(cli, ["commit-info"])
        assert result.exit_code == 1
        assert "Error: No staged changes found." in result.output

    def test_commit_info_with_staged_changes(self, runner, patch_manager):
        """Test commit-info composes proper instruction with staged changes."""
        from pathlib import Path

        repo_path = Path(patch_manager.repo_path)

        # Write real file to the temp test repo so git add picks it up
        test_file = repo_path / "hello.txt"
        test_file.write_text("Hello git tests!", encoding="utf-8")

        # Add to stage
        subprocess.run(["git", "add", "hello.txt"], cwd=str(repo_path), check=True)

        result = runner.invoke(cli, ["commit-info", "-m", "testing", "-v", "make it awesome"])

        assert result.exit_code == 0
        assert "Commit Style Guide" in result.output
        assert "Instructions" in result.output
        assert "Prefix the subject with '[testing]'" in result.output
        assert "Include a detailed body" in result.output
        assert "Additional request: make it awesome" in result.output

        # Verify the diff appears
        assert "Hello git tests!" in result.output
