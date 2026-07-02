from work_tools.core import log as log_module


def test_setup_logger_skips_file_logging_by_default(monkeypatch):
    monkeypatch.delenv("WT_FILE_LOG", raising=False)
    monkeypatch.delenv("WT_LOG_PATH", raising=False)
    monkeypatch.setattr(
        log_module,
        "get_git_repo_root",
        lambda: (_ for _ in ()).throw(AssertionError("should not resolve repo root")),
    )

    log_module.setup_logger()

    assert len(log_module.logger._core.handlers) == 1


def test_setup_logger_enables_file_logging_with_env(tmp_path, monkeypatch):
    log_path = tmp_path / "cli.log"
    monkeypatch.setenv("WT_FILE_LOG", "1")
    monkeypatch.setenv("WT_LOG_PATH", str(log_path))

    log_module.setup_logger()
    log_module.logger.info("file logging enabled")
    log_module.logger.complete()

    assert len(log_module.logger._core.handlers) == 2
    assert log_path.exists()
