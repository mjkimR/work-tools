from modules.ims.client import ImsClient


class ImsCLIHandlers:
    """CLI command handlers that bridge Click commands to ImsClient API calls.

    Each public method corresponds to a CLI subcommand and handles
    argument resolution, API interaction, and output formatting.
    """

    def __init__(self):
        """Initialize handlers with an ImsClient instance."""
        self.client = ImsClient()

    # ── Command Handlers ──────────────────────────────────────────────────────

    def get_document(self, uid: str) -> None:
        """Fetch and print a single IMS document by UID."""
        doc = self.client.get_document(uid)
        print(str(doc))

    def get_documents(self, uids: list[str]) -> None:
        """Fetch and print multiple IMS documents."""
        docs = self.client.get_documents(uids)
        for doc in docs:
            print(str(doc))
            print()
