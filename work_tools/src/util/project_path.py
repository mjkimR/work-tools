from dotenv import find_dotenv


def get_env_path():
    env_path = find_dotenv(".env", usecwd=True)
    if not env_path:
        raise Exception(
            "Cannot find environment variable file (.env). Please ensure the .env file exists in the project root."
        )
    return env_path


def get_git_repo_root():
    from pathlib import Path

    current_path = Path.cwd()
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").exists():
            return str(parent)
    raise RuntimeError("Cannot determine git repository root. Please run from a git repository.")
