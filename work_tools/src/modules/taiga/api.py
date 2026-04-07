import sys

import click

from .handler import TaigaCLIHandlers


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


# ── Projects ──────────────────────────────────────────────────────────────────


@cli.command("list-projects")
def list_projects():
    """List all projects"""
    get_handlers().list_projects()


# ── User Stories ──────────────────────────────────────────────────────────────


@cli.command("search-userstories")
@click.option("--query", "-q", default=None, help="Name keyword to search for (case-insensitive)")
@click.option("--me", is_flag=True, help="Only show user stories assigned to me")
def search_userstories(query, me):
    """Search user stories by name"""
    get_handlers().search_userstories(query=query, me=me)


@cli.command("get-userstory")
@click.option("--id", "us_id", type=int, default=None, help="User Story internal ID")
@click.option("--ref", type=int, default=None, help="User Story #ref number")
def get_userstory(us_id, ref):
    """Get a User Story by ID or #ref number"""
    get_handlers().get_userstory(id=us_id, ref=ref)


@cli.command("create-userstory")
@click.option("--subject", required=True, help="User Story subject")
@click.option("--description", default="", help="User Story description")
@click.option("--tasks", multiple=True, help="Task subjects (repeatable, simple mode)")
@click.option("--tasks-json", default=None, help='JSON array of tasks: \'[{"subject": "...", "description": "..."}]\'')
@click.option("--me", is_flag=True, help="Assign everything to myself")
def create_userstory(subject, description, tasks, tasks_json, me):
    """Create a User Story (optionally with tasks)"""
    get_handlers().create_userstory(
        subject=subject,
        description=description,
        tasks=list(tasks) if tasks else None,
        tasks_json=tasks_json,
        me=me,
    )


@cli.command("update-userstory")
@click.option("--id", "us_id", type=int, default=None, help="User Story internal ID")
@click.option("--ref", type=int, default=None, help="User Story #ref number")
@click.option("--subject", default=None, help="New subject")
@click.option("--description", default=None, help="New description")
@click.option("--status", type=int, default=None, help="New status ID")
@click.option("--me", is_flag=True, help="Assign to myself")
@click.option("--assigned-to", "assigned_to", type=int, default=None, help="Assign to user ID")
def update_userstory(us_id, ref, subject, description, status, me, assigned_to):
    """Update an existing User Story"""
    get_handlers().update_userstory(
        id=us_id,
        ref=ref,
        subject=subject,
        description=description,
        status=status,
        me=me,
        assigned_to=assigned_to,
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────


@cli.command("create-task")
@click.option("--subject", default=None, help="Task subject (single task)")
@click.option("--description", default="", help="Task description (single task)")
@click.option("--tasks", multiple=True, help="Task subjects (repeatable, bulk mode)")
@click.option("--tasks-json", default=None, help='JSON array of tasks: \'[{"subject": "...", "description": "..."}]\'')
@click.option("--us", type=int, default=None, help="User Story ID to link to")
@click.option("--us-ref", type=int, default=None, help="User Story #ref number to link to")
@click.option("--me", is_flag=True, help="Assign task(s) to myself")
def create_task(subject, description, tasks, tasks_json, us, us_ref, me):
    """Create one or multiple tasks for an existing US"""
    get_handlers().create_task(
        subject=subject,
        description=description,
        tasks=list(tasks) if tasks else None,
        tasks_json=tasks_json,
        us=us,
        us_ref=us_ref,
        me=me,
    )


# ── Custom Attributes ─────────────────────────────────────────────────────────


@cli.command("list-custom-attributes")
def list_custom_attributes():
    """List custom attribute definitions"""
    get_handlers().list_custom_attributes()


@cli.command("get-custom-attr-values")
@click.option("--id", "us_id", type=int, default=None, help="User Story internal ID")
@click.option("--ref", type=int, default=None, help="User Story #ref number")
def get_custom_attr_values(us_id, ref):
    """Get custom attribute values for a User Story"""
    get_handlers().get_custom_attr_values(id=us_id, ref=ref)


@cli.command("update-custom-attr-values")
@click.option("--id", "us_id", type=int, default=None, help="User Story internal ID")
@click.option("--ref", type=int, default=None, help="User Story #ref number")
@click.option("--values-json", required=True, help='JSON object: \'{"<attr_id>": "value"}\'')
def update_custom_attr_values(us_id, ref, values_json):
    """Update custom attribute values for a User Story"""
    get_handlers().update_custom_attr_values(values_json=values_json, id=us_id, ref=ref)


def main():
    cli()


if __name__ == "__main__":
    main()
