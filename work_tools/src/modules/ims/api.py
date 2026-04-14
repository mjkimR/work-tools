import sys

import click
from core import setup

from modules.ims.handler import ImsCLIHandlers


def get_handlers():
    """Instantiate ImsCLIHandlers, exiting with an error message on failure."""
    try:
        return ImsCLIHandlers()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """IMS Document Client"""
    pass


# ── Documents ─────────────────────────────────────────────────────────────────


@cli.command("get-document")
@click.option("--uid", required=True, help="Document UID (numeric string)")
def get_document(uid):
    """Fetch and display an IMS document by UID"""
    get_handlers().get_document(uid)


@cli.command("get-documents")
@click.option("--uid", "uids", multiple=True, required=True, help="Document UIDs (repeatable)")
def get_documents(uids):
    """Fetch and display multiple IMS documents"""
    get_handlers().get_documents(list(uids))


def main():
    """Entry point for the IMS CLI."""
    setup()
    cli()


if __name__ == "__main__":
    main()
