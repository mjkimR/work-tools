from dotenv import find_dotenv


def get_env_path():
    """Find and return the path to the .env file.

    Searches from the current working directory upward for a `.env` file.

    Returns:
        str: Absolute path to the `.env` file.

    Raises:
        Exception: If no `.env` file is found.
    """
    env_path = find_dotenv(".env", usecwd=True)
    if not env_path:
        raise Exception(
            "Cannot find environment variable file (.env). Please ensure the .env file exists in the project root."
        )
    return env_path


def get_git_repo_root():
    """Find and return the root directory of the current git repository.

    Traverses from the current working directory upward looking for a `.git` folder.

    Returns:
        str: Absolute path to the git repository root.

    Raises:
        RuntimeError: If no `.git` directory is found in any parent.
    """
    from pathlib import Path

    current_path = Path.cwd()
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").exists():
            return str(parent)
    raise RuntimeError("Cannot determine git repository root. Please run from a git repository.")
