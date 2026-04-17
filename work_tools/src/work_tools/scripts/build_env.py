import os
import subprocess

from loguru import logger
from work_tools.core import setup
from work_tools.core.util.project_path import get_git_repo_root
from work_tools.modules.taiga import TaigaClient


def _build_taiga_env():
    """Build Taiga-related environment variables interactively."""
    client = TaigaClient()

    # 1. My ID (Not stored in .env, just for confirmation)
    me = client.get_me()
    my_id = me["id"]
    print(f"Logged in as: {me['full_name']} (ID: {my_id})")

    # 2. Projects
    projects = client.get_projects()
    if not projects:
        raise Exception("No projects found for the user.")

    print("Available Projects:")
    for p in projects:
        print(f"ID: {p['id']} | Name: {p['name']}")

    default_project_id = os.getenv("TAIGA_PROJECT_ID", "")
    project_id = input(f"Enter the project ID to set in .env (default: '{default_project_id}'): ").strip()
    if not project_id and default_project_id:
        project_id = default_project_id
    if not any(str(p["id"]) == project_id for p in projects):
        raise Exception(f"Project ID '{project_id}' not found in the list of projects.")
    client.set_project_id(project_id)

    # 3. User Story Custom Attributes
    custom_attrs = client.get_userstory_custom_attributes()
    custom_attr_envs = {}
    if custom_attrs:
        print("Found Custom Attributes:")
        for attr in custom_attrs:
            attr_id = attr["id"]
            attr_name = attr["name"]
            env_key = "TAIGA_CA_" + attr_name.upper().replace(" ", "_").replace("-", "_")
            custom_attr_envs[env_key] = attr_id
            print(f"  {env_key}={attr_id}  ({attr_name})")
    else:
        print("  No Custom Attributes found")

    return {
        "TAIGA_PROJECT_ID": project_id,
        **custom_attr_envs,
    }, "# -- TAIGA Environments"


def _build_git_env():
    """Build Git-related environment variables interactively."""
    # 1. Get git user.email
    git_email = subprocess.run(
        ["git", "config", "--global", "user.email"], capture_output=True, text=True
    ).stdout.strip()
    print(f"Git user.email: {git_email}")

    # 2. git target repo (optional)
    default_repo = os.getenv("GIT_TARGET_REPO", "")
    git_target_repo = input(f"Enter Git target repository URL (optional, default: '{default_repo}'): ").strip()

    # 3. git language
    default_lang = os.getenv("GIT_LANG", "kr")

    if not git_target_repo:
        git_target_repo = default_repo
    return {
        "GIT_USER_EMAIL": git_email,
        "GIT_TARGET_REPO": git_target_repo,
        "GIT_LANG": default_lang,
    }, "# -- Git Environments"


def _make_env_line(key, value):
    """Format a key-value pair as a .env file line."""
    if isinstance(value, tuple) or isinstance(value, list):
        if len(value) >= 2:
            return f"# {value[1]}\n{key}={value[0]}"
        else:
            return f"{key}={value[0]}"
    return f"{key}={value}"


def build_env_file():
    """Build and write the .env file by collecting Taiga and Git settings."""
    setup(ignore_error=True)
    logger.info("Create Env File...")

    try:
        taiga_env = _build_taiga_env()
        git_env = _build_git_env()

        env_lines = []
        first_section = True
        for _env, _comment in [taiga_env, git_env]:
            env_lines.append(_comment if first_section else "\n\n" + _comment)
            first_section = False
            for key, value in _env.items():
                env_lines.append(_make_env_line(key, value))
        env_content = "\n".join(env_lines)

        env_path = os.path.join(get_git_repo_root(), ".env")
        with open(env_path, "w") as f:
            f.write(env_content)

        logger.info(f".env file has been created at: {env_path}")

    except Exception as e:
        raise Exception(f"Failed to build .env file: {e}") from e


if __name__ == "__main__":
    build_env_file()
