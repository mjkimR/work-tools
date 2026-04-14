import pathlib
import re
import subprocess

from modules.git_repo.config import GitRepoSettings, get_git_settings


class GitRepoManager:
    """Manages git repository operations such as log retrieval and diff extraction.

    Attributes:
        settings: Git repository settings containing repo path and user email.
    """

    def __init__(self, settings: GitRepoSettings | None = None):
        """Initialize with git repository settings."""
        self.settings = settings or get_git_settings()

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a git command against the configured repository.

        Args:
            *args: Git sub-command and arguments (without ``git -C <path>``).

        Returns:
            The completed process result.

        Raises:
            RuntimeError: If the command exits with a non-zero return code.
        """
        cmd = ["git", "-C", self.repo_path, *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git command failed: {' '.join(args)}\n{result.stderr.strip()}")
        return result

    @property
    def repo_path(self) -> str:
        """Return the target repository path from settings."""
        return self.settings.path

    @property
    def author_email(self) -> str:
        """Return the author email from settings."""
        return self.settings.user_email

    @staticmethod
    def parse_commit_range(input_str: str) -> tuple[str, str | None]:
        """Parse a commit input string into a (start, end) range tuple.

        Supported formats:
            - Single commit: "abc1234"           → ("abc1234", None)
            - Range (..):    "abc1234..def5678"  → ("abc1234", "def5678")
            - Range (~N):    "abc1234~3"         → ("abc1234~3", "abc1234")

        Args:
            input_str: Raw commit input string.

        Returns:
            A tuple of (start, end) where end is None for a single commit.
        """
        input_str = input_str.strip()

        # "SHA..SHA" format
        if ".." in input_str:
            parts = input_str.split("..", 1)
            return parts[0].strip(), parts[1].strip()

        # "SHA~N" format
        tilde_match = re.match(r"^([0-9a-fA-F]+)~(\d+)$", input_str)
        if tilde_match:
            sha = tilde_match.group(1)
            n = tilde_match.group(2)
            return f"{sha}~{n}", sha

        # Single commit
        return input_str, None

    def get_git_log(self, start: str, end: str | None) -> list[dict]:
        """Retrieve git log entries from the repository.

        For a single commit, returns only that commit. For a range, returns
        all commits between start (exclusive) and end (inclusive),
        filtered by the configured author email.

        Args:
            start: Starting commit SHA or ref.
            end: Ending commit SHA or ref. None for a single commit lookup.

        Returns:
            A list of commit dicts with keys: sha, author_name, author_email,
            date, subject, body.

        Raises:
            RuntimeError: If the git log command fails.
        """
        if end is None:
            # Single commit lookup
            rev_range = [start]
            extra_flags = ["-n", "1"]
        else:
            # Range lookup: start..end (start exclusive, end inclusive)
            rev_range = [f"{start}..{end}"]
            extra_flags = []

        cmd = [
            "log",
            "--author",
            self.author_email,
            "--pretty=format:%H%x00%an%x00%ae%x00%ad%x00%s%x00%b%x00END",
            "--date=iso",
            *extra_flags,
            *rev_range,
        ]

        result = self._run_git(*cmd)

        raw = result.stdout.strip()
        if not raw:
            return []

        commits = []
        # Split each commit block by END delimiter
        for block in raw.split("\x00END"):
            block = block.strip()
            if not block:
                continue
            parts = block.split("\x00")
            if len(parts) < 5:
                continue
            sha, author_name, author_email_val, date, subject = parts[0], parts[1], parts[2], parts[3], parts[4]
            body = parts[5].strip() if len(parts) > 5 else ""
            commits.append(
                {
                    "sha": sha,
                    "author_name": author_name,
                    "author_email": author_email_val,
                    "date": date,
                    "subject": subject,
                    "body": body,
                }
            )

        return commits

    def get_commit_diff(self, sha: str) -> str:
        """Retrieve the diff (stat + patch) for a specific commit.

        Args:
            sha: The commit SHA to inspect.

        Returns:
            The diff output as a string.

        Raises:
            RuntimeError: If the git show command fails.
        """
        result = self._run_git("show", "--stat", "--patch", sha)
        return result.stdout.strip()

    def fetch_commits_with_diff(self, commit_input: str) -> list[dict]:
        """Parse commit input and return commits with their diffs attached.

        Args:
            commit_input: Raw commit input string (single SHA, range, or ~N).

        Returns:
            A list of commit dicts, each augmented with a 'diff' key.
        """
        start, end = self.parse_commit_range(commit_input)
        commits = self.get_git_log(start, end)

        if not commits:
            print(f"[Warning] No commits found for author '{self.author_email}'.")
            return []

        for commit in commits:
            commit["diff"] = self.get_commit_diff(commit["sha"])

        return commits

    @staticmethod
    def print_commits(commits: list[dict]) -> None:
        """Print commit details in a human-readable format."""
        for i, c in enumerate(commits, 1):
            print(f"\n{'=' * 60}")
            print(f"[{i}/{len(commits)}] {c['sha'][:12]}  {c['date']}")
            print(f"Author : {c['author_name']} <{c['author_email']}>")
            print(f"Subject: {c['subject']}")
            if c["body"]:
                print(f"Body   :\n{c['body']}")
            print("\n--- diff ---")
            print(c["diff"])

    # ── Commit-info helpers ─────────────────────────────────────────────

    def get_staged_diff(self) -> str:
        """Return the staged (``--cached``) diff output.

        Returns:
            The diff string, or empty string if nothing is staged.
        """
        result = self._run_git("diff", "--cached")
        return result.stdout.strip()

    def get_recent_logs(self, count: int = 10, since: str | None = None) -> str:
        """Return recent commit subjects as a newline-separated list.

        Args:
            count: Number of recent commits to retrieve (ignored when *since* is set).
            since: If provided, return all commits in ``since..HEAD`` instead of
                the last *count* commits.

        Returns:
            Formatted string of recent commit subjects prefixed with ``-``.
        """
        if since:
            result = self._run_git("log", f"{since}..HEAD", "--pretty=format:- %s")
        else:
            result = self._run_git("log", f"-n{count}", "--pretty=format:- %s")
        return result.stdout.strip()

    def get_commit_style_guide(self) -> str:
        """Read and return the commit style guide markdown.

        Returns:
            Contents of ``commit_style.md`` located alongside this module.
        """
        style_path = pathlib.Path(__file__).parent / "commit_style.md"
        content = style_path.read_text(encoding="utf-8")
        return content.replace("{lang}", self.settings.lang)

    # ── Branch helpers ──────────────────────────────────────────────────

    def get_current_branch(self) -> str:
        """Return the name of the currently checked-out branch.

        Returns:
            Branch name string (e.g. ``f/my-feature``).

        Raises:
            RuntimeError: If the git command fails.
        """
        result = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()

    def is_feature_branch(self) -> bool:
        """Return True if the current branch starts with ``f/``.

        Returns:
            ``True`` when on a feature branch, ``False`` otherwise.
        """
        return self.get_current_branch().startswith("f/")

    def get_feature_base_commit(self) -> str:
        """Find the merge-base commit between HEAD and the main base branch.

        Tries local and remote-tracking refs for ``main``, ``master``, and ``dev``
        in order, picking the **most recent** (closest to HEAD) merge-base among
        all candidates so that stale local refs do not push the divergence point
        further back than expected.

        Returns:
            The merge-base commit SHA string.

        Raises:
            RuntimeError: If no valid base ref is found, or if the git command fails.
        """
        candidates = [ref for name in ("main", "master", "dev") for ref in (name, f"origin/{name}")]

        merge_bases: list[str] = []
        for ref in candidates:
            verify = subprocess.run(
                ["git", "-C", self.repo_path, "rev-parse", "--verify", ref],
                capture_output=True,
                text=True,
            )
            if verify.returncode != 0:
                continue
            mb = subprocess.run(
                ["git", "-C", self.repo_path, "merge-base", "HEAD", ref],
                capture_output=True,
                text=True,
            )
            if mb.returncode == 0 and mb.stdout.strip():
                merge_bases.append(mb.stdout.strip())

        if not merge_bases:
            raise RuntimeError("Cannot detect base branch: none of main/master/dev (local or origin) found.")

        if len(merge_bases) == 1:
            return merge_bases[0]

        # Among all candidates pick the most recent merge-base (closest to HEAD).
        # Walk commits reachable from HEAD in topo order and return the first
        # SHA that appears in our candidate set.
        result = self._run_git("log", "--topo-order", "--format=%H", "HEAD")
        ordered = [sha.strip() for sha in result.stdout.splitlines() if sha.strip()]
        merge_base_set = set(merge_bases)
        for sha in ordered:
            if sha in merge_base_set:
                return sha

        # Fallback: return the first candidate found
        return merge_bases[0]

    def fetch_feature_branch_commits(self) -> list[dict]:
        """Fetch commits introduced on the current feature branch.

        Detects the divergence point from the base branch (``main`` / ``master``)
        and returns all author-filtered commits from that point to ``HEAD``.

        Returns:
            A list of commit dicts (same schema as :meth:`fetch_commits_with_diff`),
            each augmented with a ``diff`` key.

        Raises:
            RuntimeError: If the current branch is not a feature branch (does not
                start with ``f/``), or if any underlying git command fails.
        """
        if not self.is_feature_branch():
            branch = self.get_current_branch()
            raise RuntimeError(f"Current branch '{branch}' is not a feature branch (must start with 'f/').")

        base_commit = self.get_feature_base_commit()
        commit_input = f"{base_commit}..HEAD"
        return self.fetch_commits_with_diff(commit_input)
