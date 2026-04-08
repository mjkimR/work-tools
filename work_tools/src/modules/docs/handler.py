from .loader import DocsLoader


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

    def list_subjects(self) -> None:
        """List all available subjects defined in the manifest."""
        subjects = self.loader.list_subjects()
        if not subjects:
            print("No subjects defined in the manifest.")
            return
        print("Available subjects:")
        for s in subjects:
            entry = self.loader.manifest.subjects.get(s)
            desc = entry.description.strip() if entry and entry.description else ""
            print(f"  - {s}: {desc}" if desc else f"  - {s}")
