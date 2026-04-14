import sys

import click
from core import setup

from modules.docs.handler import DocsCLIHandlers
from modules.docs.loader import DocsLoader


def get_handlers():
    """Instantiate DocsCLIHandlers, exiting with an error message on failure."""
    try:
        return DocsCLIHandlers()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _build_read_docs_help() -> str:
    """Build help text for read-docs, listing available subjects with descriptions from the manifest."""
    try:
        subjects = DocsLoader().list_subjects_with_descriptions()
        if subjects:
            lines = [f"* {name}: {desc}" for name, desc in subjects.items()]
            subjects_block = "\n\n".join(lines)
        else:
            subjects_block = "  (none)"
    except Exception:
        subjects_block = "  (unavailable)"
    # \b prevents Click from re-wrapping the text below it
    return (
        "Read and compose context for a SUBJECT defined in docs_manifest.yaml.\n"
        "\n"
        "Available subjects:\n\n"
        f"{subjects_block}"
    )


@click.group()
def cli():
    """Docs Context Reader / Agent Skill"""
    pass


@cli.command("read-docs", help=_build_read_docs_help())
@click.argument("subject")
def read_docs(subject):
    get_handlers().read_docs(subject)


def main():
    """Entry point for the Docs CLI."""
    setup()
    cli()


if __name__ == "__main__":
    main()
