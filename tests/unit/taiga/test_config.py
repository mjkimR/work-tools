"""Tests for TaigaSettings defaults."""

from work_tools.modules.taiga.config import TaigaSettings


class TestTaigaSettings:
    """Validate settings defaults."""

    def test_domain_default(self):
        settings = TaigaSettings()  # type: ignore[call-arg]
        assert settings.domain == "taiga"
