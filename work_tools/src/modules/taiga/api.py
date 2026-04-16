import sys

import click
from core import setup

from modules.taiga.handler import TaigaCLIHandlers


def get_handlers():
    try:
        return TaigaCLIHandlers()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Taiga API Client / Agent Skill"""
    pass


# ── User Stories ──────────────────────────────────────────────────────────────


@cli.command("create-userstory")
@click.option("--subject", required=True, help="User Story subject")
@click.option("--description", default="", help="User Story description")
@click.option("--status", type=int, default=None, help="Initial status ID")
@click.option("--tasks", multiple=True, help="Task subjects (repeatable, simple mode)")
@click.option("--tasks-json", default=None, help='JSON array of tasks: \'[{"subject": "...", "description": "..."}]\'')
@click.option("--custom-attrs-json", default=None, help='JSON object of custom attributes: \'{"<attr_id>": "value"}\'')
@click.option("--me", is_flag=True, help="Assign everything to myself")
@click.option("--assigned-to", type=int, default=None, help="Assign to specific user ID")
def create_userstory(subject, description, status, tasks, tasks_json, custom_attrs_json, me, assigned_to):
    """Create a User Story with tasks and custom attributes in one go"""
    get_handlers().create_userstory(
        subject=subject,
        description=description,
        status=status,
        tasks=list(tasks) if tasks else None,
        tasks_json=tasks_json,
        custom_attrs_json=custom_attrs_json,
        me=me,
        assigned_to=assigned_to,
    )


@cli.command("update-userstory")
@click.option("--ref", required=True, type=int, help="User Story #ref number")
@click.option("--subject", default=None, help="New subject")
@click.option("--description", default=None, help="New description")
@click.option("--status", type=int, default=None, help="New status ID")
@click.option(
    "--custom-attrs-json", default=None, help='JSON object to update custom attributes: \'{"<attr_id>": "value"}\''
)
@click.option("--me", is_flag=True, help="Assign to myself")
@click.option("--assigned-to", type=int, default=None, help="Assign to user ID")
def update_userstory(ref, subject, description, status, custom_attrs_json, me, assigned_to):
    """Update an existing User Story's fields and/or custom attributes"""
    get_handlers().update_userstory(
        ref=ref,
        subject=subject,
        description=description,
        status=status,
        custom_attrs_json=custom_attrs_json,
        me=me,
        assigned_to=assigned_to,
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────


@cli.command("create-task")
@click.option("--us-ref", required=True, type=int, help="User Story #ref number to link to")
@click.option("--subject", default=None, help="Task subject (single task)")
@click.option("--description", default="", help="Task description (single task)")
@click.option("--tasks", multiple=True, help="Task subjects (repeatable, bulk mode)")
@click.option("--tasks-json", default=None, help='JSON array of tasks: \'[{"subject": "...", "description": "..."}]\'')
@click.option("--me", is_flag=True, help="Assign task(s) to myself")
def create_task(us_ref, subject, description, tasks, tasks_json, me):
    """Create one or multiple tasks for an existing US by #ref"""
    get_handlers().create_task(
        us_ref=us_ref,
        subject=subject,
        description=description,
        tasks=list(tasks) if tasks else None,
        tasks_json=tasks_json,
        me=me,
    )


@cli.command("update-task")
@click.option("--ref", required=True, type=int, help="Task #ref number")
@click.option("--subject", default=None, help="New subject")
@click.option("--description", default=None, help="New description")
@click.option("--status", type=int, default=None, help="New status ID")
@click.option("--me", is_flag=True, help="Assign to myself")
@click.option("--assigned-to", type=int, default=None, help="Assign to specific user ID")
def update_task(ref, subject, description, status, me, assigned_to):
    """Update an existing Task's fields by #ref"""
    get_handlers().update_task(
        ref=ref,
        subject=subject,
        description=description,
        status=status,
        me=me,
        assigned_to=assigned_to,
    )


def main():
    setup()
    cli()


if __name__ == "__main__":
    main()
