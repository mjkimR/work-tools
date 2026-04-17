from work_tools.modules.docs.loader import DocsLoader


class DocsCLIHandlers:
    """CLI command handlers that bridge Click commands to DocsLoader.

    Each public method corresponds to a CLI subcommand and handles
    argument resolution, loader interaction, and output formatting.
    """

    def __init__(self):
        """Initialize handlers with a DocsLoader instance."""
        self.loader = DocsLoader()

    def read_docs(self, subject: str) -> None:
        """Load and print the composed context for a subject.

        Args:
            subject: The subject key from docs_manifest.yaml.
        """
        output = self.loader.load(subject)
        print(output)
