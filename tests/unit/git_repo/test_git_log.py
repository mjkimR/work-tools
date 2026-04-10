"""Tests for GitRepoManager — pure logic (no real git repo needed)."""

import pytest

from modules.git_repo.git_log import GitRepoManager


class TestParseCommitRange:
    """parse_commit_range is a static method with no side effects."""

    def test_single_sha(self):
        start, end = GitRepoManager.parse_commit_range("abc1234")
        assert start == "abc1234"
        assert end is None

    def test_range_dotdot(self):
        start, end = GitRepoManager.parse_commit_range("abc1234..def5678")
        assert start == "abc1234"
        assert end == "def5678"

    def test_range_tilde(self):
        start, end = GitRepoManager.parse_commit_range("abc1234~3")
        assert start == "abc1234~3"
        assert end == "abc1234"

    def test_whitespace_trimmed(self):
        start, end = GitRepoManager.parse_commit_range("  abc1234  ")
        assert start == "abc1234"
        assert end is None

    def test_dotdot_with_spaces(self):
        start, end = GitRepoManager.parse_commit_range(" abc .. def ")
        assert start == "abc"
        assert end == "def"

    def test_tilde_zero(self):
        start, end = GitRepoManager.parse_commit_range("abc1234~0")
        assert start == "abc1234~0"
        assert end == "abc1234"


class TestGetCommitStyleGuide:
    """commit_style.md loading."""

    def test_returns_non_empty_string(self):
        guide = GitRepoManager.get_commit_style_guide()
        assert isinstance(guide, str)
        assert len(guide) > 0
        assert "Conventional Commits" in guide