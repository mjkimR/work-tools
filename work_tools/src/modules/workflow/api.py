import sys

import click
from core import setup

from modules.ims.client import ImsClient
from modules.taiga.client import TaigaClient
from modules.workflow.handler.user_story import UserStoryHandler


def get_handler():
    """Instantiate UserStoryHandler, exiting with an error message on failure."""
    try:
        return UserStoryHandler(
            taiga_client=TaigaClient(),
            ims_client=ImsClient(),
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Workflow CLI – cross-module automation commands"""
    pass


# ── User Story ────────────────────────────────────────────────────────────────


@cli.command("get-context")
@click.option("--ref", required=True, help="User Story #ref number")
def get_full_context(ref):
    """Get full context of a User Story (US, tasks, comments, IMS docs)"""
    get_handler().get_full_context(user_story_ref=ref)


def main():
    """Entry point for the Workflow CLI."""
    setup()
    cli()


if __name__ == "__main__":
    main()
