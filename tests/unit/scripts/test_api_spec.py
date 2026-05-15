from pathlib import PurePath
from unittest.mock import MagicMock, patch

import pytest
from work_tools.scripts.api_spec import _run_help


def test_run_help_valid_wt():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="help text", stderr="")
        result = _run_help("wt", "ims", "list")
        assert result == "help text"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["uv", "run", "wt", "ims", "list", "--help"]


def test_run_help_invalid_cli_name():
    with pytest.raises(ValueError, match="Unauthorized cli_name: ls"):
        _run_help("ls")


def test_run_help_invalid_arg_character():
    with pytest.raises(ValueError, match="Invalid character in argument: ims;"):
        _run_help("wt", "ims;")


def test_run_help_invalid_arg_space():
    with pytest.raises(ValueError, match="Invalid character in argument: ims list"):
        _run_help("wt", "ims list")


def test_run_help_fallback_to_venv():
    with patch("subprocess.run") as mock_run:
        # First call (uv run) fails, second call (venv) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="uv error"),
            MagicMock(returncode=0, stdout="venv help text", stderr=""),
        ]
        result = _run_help("wt", "ims")
        assert result == "venv help text"
        assert mock_run.call_count == 2

        # Verify first call
        args1, _ = mock_run.call_args_list[0]
        assert args1[0] == ["uv", "run", "wt", "ims", "--help"]

        # Verify second call
        args2, _ = mock_run.call_args_list[1]
        venv_path = PurePath(args2[0][0])
        assert venv_path.parts[-3:] == (".venv", "bin", "wt")
        assert args2[0][1:] == ["ims", "--help"]
