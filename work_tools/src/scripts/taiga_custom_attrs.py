"""
taiga_custom_attrs.py
---------------------
Dynamic generator for docs_manifest.yaml.

Fetches the list of custom attributes defined in the Taiga project and
returns a formatted Markdown section suitable for AI context injection.

Usage (docs_manifest.yaml):
    generators:
      - "scripts.taiga_custom_attrs:generate_custom_attributes"
"""

from core import setup
from modules.taiga.client import TaigaClient


def generate_custom_attributes() -> str:
    """Fetch Taiga custom attributes and return a formatted Markdown string.

    Returns:
        A Markdown table listing each custom attribute's ID, name, and type.
    """
    setup()
    client = TaigaClient()
    attrs = client.get_userstory_custom_attributes()

    if not attrs:
        return "_No custom attributes defined for this project._"

    lines = [
        "## Custom Attributes",
        "",
        "Use these attribute IDs with `update-custom-attr-values`.",
        "",
    ]

    for attr in attrs:
        attr_id = attr["id"]
        name = attr["name"]
        attr_type = attr.get("type", "text")
        lines.append(f"- {name} (ID: {attr_id}, type: {attr_type})")

    lines += [
        "",
        "Example:",
        '  taiga-cli update-custom-attr-values --ref <REF> --values-json \'{"<ATTR_ID>": "value"}\'',
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_custom_attributes())
