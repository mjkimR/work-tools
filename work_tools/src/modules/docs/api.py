import sys

import click

from .handler import DocsCLIHandlers


def get_handlers():
    """Instantiate DocsCLIHandlers, exiting with an error message on failure."""
    try:
        return DocsCLIHandlers()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Docs Context Reader / Agent Skill"""
    pass


@cli.command("read-docs")
@click.argument("subject")
def read_docs(subject):
    """Read and compose context for a SUBJECT defined in docs_manifest.yaml."""
    get_handlers().read_docs(subject)


@cli.command("list-subjects")
def list_subjects():
    """List all available subjects in the manifest."""
    get_handlers().list_subjects()


def main():
    """Entry point for the Docs CLI."""
    cli()


if __name__ == "__main__":
    main()
