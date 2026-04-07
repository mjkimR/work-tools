from dotenv import load_dotenv
from util.project_path import get_env_path

from core.log import setup_logger

__initialized = False


def load_env():
    env_path = get_env_path()
    if not load_dotenv(env_path):
        raise RuntimeError(f"Failed to load environment variables from {env_path}")


def setup(ignore_error=False):
    global __initialized
    if __initialized:
        return

    for _func in [load_env, setup_logger]:
        try:
            _func()
        except Exception as e:
            if not ignore_error:
                raise RuntimeError(f"Error during setup: {_func.__name__} - {str(e)}") from e

    __initialized = True
