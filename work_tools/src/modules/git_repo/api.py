import sys

import click

from .git_log import GitRepoManager


def get_manager():
    """Instantiate GitRepoManager, exiting with an error message on failure."""
    try:
        return GitRepoManager()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Git Repository Log Viewer"""
    pass


@cli.command("log")
@click.argument("commit_input")
def log(commit_input):
    """Fetch commit logs with diffs.

    COMMIT_INPUT formats: <SHA>, <SHA1>..<SHA2>, <SHA>~<N>
    """
    manager = get_manager()

    click.echo(f"Repository   : {manager.repo_path}")
    click.echo(f"Author email : {manager.author_email}")
    click.echo(f"Commit input : {commit_input}")

    try:
        commits = manager.fetch_commits_with_diff(commit_input)
    except RuntimeError as e:
        click.echo(f"[Error] {e}", err=True)
        sys.exit(1)

    if not commits:
        click.echo("No commits matching the criteria.")
        sys.exit(0)

    click.echo(f"\nFound {len(commits)} commit(s).")
    manager.print_commits(commits)


def main():
    """Entry point for the Git Repo CLI."""
    cli()


if __name__ == "__main__":
    main()
