"""Tests for ImsUtils — URL extraction and UUID parsing."""

import pytest
from modules.ims.config import ImsSettings
from modules.ims.utils import ImsUtils


@pytest.fixture
def utils():
    settings = ImsSettings()  # type: ignore[call-arg]
    return ImsUtils("https://ims.example.com/board", settings=settings)


class TestGetImsUrl:
    """URL extraction from arbitrary text."""

    def test_single_url(self, utils):
        text = "See https://ims.example.com/board?uid=123&mod=document for details."
        urls = utils.get_ims_url(text)
        assert len(urls) == 1
        assert "uid=123" in urls[0]

    def test_multiple_urls(self, utils):
        text = "Issue A: https://ims.example.com/board?uid=100 Issue B: https://ims.example.com/board?uid=200"
        urls = utils.get_ims_url(text)
        assert len(urls) == 2

    def test_no_match(self, utils):
        text = "Visit https://other-site.com/board?uid=123"
        urls = utils.get_ims_url(text)
        assert len(urls) == 0

    def test_url_pattern_cached(self, utils):
        _ = utils.get_url_pattern()
        pattern1 = utils.url_pattern
        _ = utils.get_url_pattern()
        pattern2 = utils.url_pattern
        assert pattern1 is pattern2


class TestParseUuidFromUrl:
    """UUID extraction from IMS URLs."""

    def test_uuid_basic(self):
        url = "https://ims.example.com/view?uid=550e8400-e29b-41d4-a716-446655440000"
        assert ImsUtils.parse_uuid_from_url(url) == "550e8400-e29b-41d4-a716-446655440000"

    def test_uuid_with_other_params(self):
        url = "https://ims.example.com/view?mod=doc&uid=abcdef12-3456-7890-abcd-ef1234567890&page=1"
        assert ImsUtils.parse_uuid_from_url(url) == "abcdef12-3456-7890-abcd-ef1234567890"

    def test_no_uuid(self):
        url = "https://ims.example.com/view?uuid=123"
        assert ImsUtils.parse_uuid_from_url(url) is None

    def test_short_hex(self):
        url = "https://ims.example.com/view?uid=abcdef"
        assert ImsUtils.parse_uuid_from_url(url) == "abcdef"
