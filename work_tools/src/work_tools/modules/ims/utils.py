import re

from work_tools.modules.ims.config import ImsSettings, get_ims_settings


class ImsUtils:
    """Utility class for IMS URL handling.

    Provides helpers to detect IMS URLs in arbitrary text and extract
    query parameters (e.g. uuid) from those URLs.
    """

    def __init__(self, base_url: str, settings: ImsSettings | None = None):
        self.settings = settings or get_ims_settings()
        self.base_url = base_url
        self.url_pattern = None

    def get_url_pattern(self) -> re.Pattern:
        """Build and cache the compiled regex pattern for IMS URLs."""
        if self.url_pattern is None:
            self.url_pattern = re.compile(rf"{re.escape(self.base_url)}[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+")
        return self.url_pattern

    def get_ims_url(self, text: str) -> list[str]:
        """Extract all IMS URLs from the given text."""
        urls = self.get_url_pattern().findall(text)
        return urls

    @classmethod
    def parse_uuid_from_url(cls, url: str) -> str | None:
        """Extract UUID from the given IMS URL.

        Parses the uid value from a query parameter in the form ``?uid=0000``.
        """
        match = re.search(r"[?&]uid=([a-fA-F0-9\-]+)", url)
        if match:
            return match.group(1)
        return None
