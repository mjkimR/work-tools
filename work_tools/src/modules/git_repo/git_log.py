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
            "git",
            "-C",
            self.repo_path,
            "log",
            "--author",
            self.author_email,
            "--pretty=format:%H%x00%an%x00%ae%x00%ad%x00%s%x00%b%x00END",
            "--date=iso",
            *extra_flags,
            *rev_range,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"git log execution error:\n{result.stderr.strip()}")

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
        cmd = ["git", "-C", self.repo_path, "show", "--stat", "--patch", sha]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git show error ({sha}):\n{result.stderr.strip()}")
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
