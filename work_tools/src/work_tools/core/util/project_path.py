from pathlib import Path

from dotenv import find_dotenv


def _find_project_root_from_file() -> Path | None:
    """Traverse up from the current file to find the project root directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / "uv.lock").exists() or (parent / ".git").exists():
            return parent
    return None


def get_env_path():
    """Find and return the path to the .env file.

    First tries to find the .env file relative to the source code location,
    then falls back to searching upward from the current working directory.

    Returns:
        str: Absolute path to the `.env` file.

    Raises:
        Exception: If no `.env` file is found.
    """
    # 1. Try to find relative to source code path (portable)
    root = _find_project_root_from_file()
    if root:
        env_path = root / ".env"
        if env_path.exists():
            return str(env_path)

    # 2. Fallback to searching from CWD
    env_path = find_dotenv(".env", usecwd=True)
    if not env_path:
        raise Exception(
            "Cannot find environment variable file (.env). Please ensure the .env file exists in the project root."
        )
    return env_path


def get_git_repo_root():
    """Find and return the root directory of the current git repository.

    First tries to find a git repository starting from the current working directory,
    then falls back to searching relative to the source code location.

    Returns:
        str: Absolute path to the git repository root.

    Raises:
        RuntimeError: If no `.git` directory is found in any parent.
    """
    # 1. Try to find starting from CWD (essential for testing and target repo mapping)
    current_path = Path.cwd()
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").exists():
            return str(parent)

    # 2. Fallback to searching relative to the source code location
    root = _find_project_root_from_file()
    if root and (root / ".git").exists():
        return str(root)

    raise RuntimeError("Cannot determine git repository root. Please run from a git repository.")
