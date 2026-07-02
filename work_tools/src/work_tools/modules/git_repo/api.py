import sys

import click
from work_tools.core import setup
from work_tools.modules.git_repo.git_log import GitRepoManager


def get_manager():
    """Instantiate GitRepoManager, exiting with an error message on failure."""
    try:
        return GitRepoManager()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def print_commits(commits: list[dict]) -> None:
    """Print commit details in a human-readable format."""
    for i, c in enumerate(commits, 1):
        click.echo(f"\n{'=' * 60}")
        click.echo(f"[{i}/{len(commits)}] {c['sha'][:12]}  {c['date']}")
        click.echo(f"Author : {c['author_name']} <{c['author_email']}>")
        click.echo(f"Subject: {c['subject']}")
        if c.get("body"):
            click.echo(f"Body   :\n{c['body']}")
        if "raw_diff" in c:
            click.echo("\n--- diff ---")
            click.echo(c["raw_diff"])
        elif "diff" in c:
            click.echo("\n--- diff ---")
            click.echo(c["diff"])


@click.group()
def cli():
    """Git Repository Log Viewer"""
    pass


@cli.command("log")
@click.option(
    "-b", "--branch", "use_branch", is_flag=True, help="Auto-detect feature branch range (f/... → base..HEAD)."
)
@click.argument("commit_input", required=False, default=None)
def log(use_branch, commit_input):
    """Fetch commit logs with diffs.

    COMMIT_INPUT formats: <SHA>, <SHA1>..<SHA2>, <SHA>~<N>

    Use --branch to automatically detect the commit range for the current
    feature branch (must start with 'f/').
    """
    manager = get_manager()

    click.echo(f"Repository   : {manager.repo_path}")
    click.echo(f"Author email : {manager.author_email}")

    try:
        if use_branch:
            branch_name = manager.get_current_branch()
            click.echo(f"Branch       : {branch_name} (auto-range)")
            commits = manager.fetch_feature_branch_commits()
        else:
            if not commit_input:
                raise click.UsageError("COMMIT_INPUT is required unless --branch is specified.")
            click.echo(f"Commit input : {commit_input}")
            commits = manager.fetch_commits_with_diff(commit_input)
    except RuntimeError as e:
        click.echo(f"[Error] {e}", err=True)
        sys.exit(1)

    if not commits:
        click.echo("No commits matching the criteria.")
        sys.exit(0)

    click.echo(f"\nFound {len(commits)} commit(s).")
    print_commits(commits)


@cli.command("commit-info")
@click.option(
    "-m", "--module", "module_name", default=None, help="Module name to prefix the commit subject with [module]."
)
@click.option("-v", "--verbose", is_flag=True, help="Request a detailed body in addition to the subject line.")
@click.argument("extra", nargs=-1)
def commit_info(module_name, verbose, extra):
    """Gather staged diff, recent logs, and commit style guide for AI-assisted commit message generation.

    Any trailing arguments are passed through as extra instructions.
    """
    manager = get_manager()

    # 1. Staged diff
    staged_diff = manager.get_staged_diff()
    if not staged_diff:
        click.echo("Error: No staged changes found. Run 'git add' first.", err=True)
        sys.exit(1)

    # 2. Recent commit logs
    recent_logs = manager.get_recent_logs()

    # 3. Commit style guide
    style_guide = manager.get_commit_style_guide()

    # 4. Build supplementary instructions
    instructions: list[str] = []
    if module_name:
        instructions.append(f"- Prefix the subject with '[{module_name}]'.")
    if verbose:
        instructions.append("- Include a detailed body with bullet points after a blank line.")
    else:
        instructions.append("- Output ONLY a single subject line. No body, no quotes, no explanation.")
    if extra:
        instructions.append(f"- Additional request: {' '.join(extra)}")

    # 5. Output
    click.echo("## Commit Style Guide\n")
    click.echo(style_guide)
    click.echo("\n## Instructions\n")
    click.echo("\n".join(instructions))
    click.echo("\n## Recent Commit Logs\n")
    click.echo(recent_logs)
    click.echo("\n## Staged Diff\n")
    click.echo(staged_diff)


def main():
    """Entry point for the Git Repo CLI."""
    setup()
    cli()


if __name__ == "__main__":
    main()
