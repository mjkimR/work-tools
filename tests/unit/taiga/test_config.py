"""Tests for TaigaSettings — dynamic TAIGA_CA_* env var parsing."""

from work_tools.modules.taiga.config import TaigaSettings


class TestTaigaSettingsCaParsing:
    """Validate the model_validator that collects TAIGA_CA_* env vars."""

    def test_ca_fields_from_env(self, monkeypatch):
        monkeypatch.setenv("TAIGA_CA_PRIORITY", "10")
        monkeypatch.setenv("TAIGA_CA_SPRINT_GOAL", "20")
        monkeypatch.setenv("TAIGA_DOMAIN", "taiga")

        settings = TaigaSettings()  # type: ignore[call-arg]
        assert settings.custom_attributes == {"PRIORITY": 10, "SPRINT_GOAL": 20}

    def test_ca_fields_empty_when_none(self, monkeypatch):
        monkeypatch.setenv("TAIGA_DOMAIN", "taiga")
        # Ensure no TAIGA_CA_ vars exist
        monkeypatch.delenv("TAIGA_CA_PRIORITY", raising=False)
        monkeypatch.delenv("TAIGA_CA_SPRINT_GOAL", raising=False)

        settings = TaigaSettings()  # type: ignore[call-arg]
        assert settings.custom_attributes == {}

    def test_domain_default(self):
        settings = TaigaSettings()  # type: ignore[call-arg]
        assert settings.domain == "taiga.lab.morpheus.kr"
