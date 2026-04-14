from __future__ import annotations

from core.exception import TokenExpiredError

from modules.browser.api_client import AuthMode, BrowserTokenBaseClient
from modules.ims.config import ImsSettings, get_ims_settings
from modules.ims.parser import ImsDocument, ImsDocumentParser
from modules.ims.utils import ImsUtils


class ImsClient(BrowserTokenBaseClient):
    """HTTP client for the in-house IMS (KBoard/WordPress).

    Authenticates via cookies discovered from a running Chrome browser tab.
    Provides helpers for fetching and parsing IMS document pages.

    Attributes:
        settings: IMS connection settings (domain, base_url, cookie fields).
    """

    def __init__(self, settings: ImsSettings | None = None):
        """Initialize ImsClient with settings and discover cookies from browser session.

        Args:
            settings: Optional ``ImsSettings`` override; defaults are loaded
                      from environment variables.
        """
        self.settings: ImsSettings = settings or get_ims_settings()
        self.parser = ImsDocumentParser()

        # BrowserTokenBaseClient.__init__ discovers the session and creates self.http
        super().__init__()

        self.util = ImsUtils(base_url=self.base_url, settings=self.settings)

    # ── BrowserTokenBaseClient configuration ────────────────────────────

    @property
    def domain(self) -> str:
        return self.settings.domain

    @property
    def auth_mode(self) -> AuthMode:
        return AuthMode.COOKIE

    @property
    def cookie_fields(self) -> list[str] | None:
        return self.settings.cookie_fields or None

    @property
    def cookie_prefixes(self) -> list[str] | None:
        return self.settings.cookie_prefixes or None

    @property
    def unauthorized_status_codes(self) -> set[int]:
        # WordPress may redirect to login (302) or return 403
        return {401, 403}

    @property
    def base_url_suffix(self) -> str:
        return self.settings.base_url_suffix

    # ── API methods ─────────────────────────────────────────────────────

    def get_document(self, uid: str) -> ImsDocument:
        """Fetch and parse an IMS document by its UID.

        Args:
            uid: The document UID (numeric string).

        Returns:
            Parsed ``ImsDocument`` dataclass.

        Raises:
            TokenExpiredError: If the server returns a login-required page,
                indicating that the session cookies are missing or expired.
            httpx.HTTPStatusError: If the request fails with a non-2xx status.
            ValueError: If the page HTML cannot be parsed for other reasons.
        """
        response = self.get("/", params={"uid": uid, "mod": "document"})
        response.raise_for_status()
        try:
            return self.parser.parse(response.text)
        except PermissionError as exc:
            msg = (
                f"IMS authentication failed while fetching document '{uid}'.\n"
                f"  -> The session cookies for '{self.domain}' may be missing or expired.\n"
                f"  -> Required cookies: PHPSESSID, JSESSIONID, wordpress_logged_in_*\n"
                f"  -> Please log in to the IMS site in Chrome and retry.\n"
                f"  -> Detail: {exc}"
            )
            raise TokenExpiredError(msg) from exc

    def get_documents(self, uids: list[str]) -> list[ImsDocument]:
        """Fetch and parse multiple IMS documents.

        Args:
            uids: List of document UIDs to fetch.

        Returns:
            List of parsed ``ImsDocument`` dataclasses (order matches *uids*).
        """
        return [self.get_document(uid) for uid in uids]

    def post_comment(self, uid: str, content: str) -> bool:
        """Post a comment on an IMS document.

        Args:
            uid: The document UID to comment on.
            content: Comment text body.

        Returns:
            True if the comment was posted successfully.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
        """
        data = {
            "uid": uid,
            "comment": content,
        }
        response = self.post("/", data=data, params={"uid": uid, "mod": "document"})
        response.raise_for_status()
        return response.is_success
