"""FakeImsClient — drop-in replacement for ImsClient without browser/HTTP.

Matches ImsClient's public method signatures exactly.
If a signature changes, tests using this fake will break → interface drift detected.
"""

from modules.ims.parser import ImsDocument, ImsDocumentParser

from tests.fake.data.ims import SAMPLE_DOCUMENT_HTML

# Pre-built documents keyed by UID
_parser = ImsDocumentParser()
_DOCUMENTS: dict[str, str] = {
    "8226": SAMPLE_DOCUMENT_HTML,
}


class FakeImsClient:
    """Fake that replaces ImsClient for handler-level testing.

    Bypasses browser session discovery and HTTP entirely.
    Parsing still goes through the real ``ImsDocumentParser`` so that
    parser regressions are caught even in handler tests.
    """

    def __init__(self):
        self.parser = ImsDocumentParser()

        # Mutable store — tests can add/remove entries
        self._documents: dict[str, str] = dict(_DOCUMENTS)

        # Call recordings for assertions
        self.posted_comments: list[dict[str, str]] = []

    # ── Helpers for test setup ──────────────────────────────────────────

    def add_document(self, uid: str, html: str) -> None:
        """Register a custom HTML page for the given UID."""
        self._documents[uid] = html

    # ── API methods (same signatures as ImsClient) ──────────────────────

    def get_document(self, uid: str) -> ImsDocument:
        """Fetch and parse an IMS document by its UID.

        Raises:
            ValueError: If the UID is not in the fake store or HTML is unparseable.
        """
        html = self._documents.get(uid)
        if html is None:
            raise ValueError(f"Document uid={uid} not found in fake data")
        return self.parser.parse(html)

    def get_documents(self, uids: list[str]) -> list[ImsDocument]:
        """Fetch and parse multiple IMS documents."""
        return [self.get_document(uid) for uid in uids]

    def post_comment(self, uid: str, content: str) -> bool:
        """Record a comment post (always succeeds)."""
        self.posted_comments.append({"uid": uid, "comment": content})
        return True
