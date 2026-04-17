import click
from work_tools.core import setup
from work_tools.modules.browser.api import cli as browser_cli
from work_tools.modules.docs.api import cli as docs_cli
from work_tools.modules.git_repo.api import cli as git_cli
from work_tools.modules.ims.api import cli as ims_cli
from work_tools.modules.taiga.api import cli as taiga_cli
from work_tools.modules.workflow.api import cli as workflow_cli


@click.group()
def main_cli():
    """Work Tools CLI – Unified entry point for all automation tools."""
    pass


# Add module CLIs as subcommands
main_cli.add_command(ims_cli, name="ims")
main_cli.add_command(taiga_cli, name="taiga")
main_cli.add_command(git_cli, name="git")
main_cli.add_command(docs_cli, name="docs")
main_cli.add_command(browser_cli, name="browser")
main_cli.add_command(workflow_cli, name="workflow")


@main_cli.command("init")
def init():
    """Initialize the environment (.env file) interactively."""
    from work_tools.scripts.build_env import build_env_file

    build_env_file()


@main_cli.group("dev")
def dev_cli():
    """Development and maintenance utilities."""
    pass


@dev_cli.command("gen-spec")
def gen_spec():
    """Generate API specification documentation (api_spec.md)."""
    from work_tools.scripts.api_spec import main as gen_spec_main

    gen_spec_main()


def main():
    """Main entry point that performs setup and runs the CLI."""
    setup()
    main_cli()


if __name__ == "__main__":
    main()
