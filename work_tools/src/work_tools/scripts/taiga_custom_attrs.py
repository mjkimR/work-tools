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

from work_tools.core import setup
from work_tools.modules.taiga.client import TaigaClient


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
        'Set values with `wt taiga update-userstory --ref <REF> --custom-attrs "<ATTR_ID>::<value>"`',
        "(the same `--custom-attrs` flag also works on `create-userstory`).",
        "For `dropdown` types, the value MUST exactly match one of the listed allowed values.",
        "",
    ]

    for attr in attrs:
        attr_id = attr["id"]
        name = attr["name"]
        attr_type = attr.get("type", "text")
        lines.append(f"- {name} (ID: {attr_id}, type: {attr_type})")
        if attr_type == "dropdown":
            options = attr.get("extra") or []
            if options:
                allowed = " | ".join(options)
                lines.append(f"    - Allowed values (choose exactly one): {allowed}")

    lines += [
        "",
        "Example:",
        '  wt taiga update-userstory --ref <REF> --custom-attrs "8::release note text"',
    ]

    # Append a dropdown-specific example when at least one dropdown attribute exists.
    dropdown = next((a for a in attrs if a.get("type") == "dropdown" and (a.get("extra") or [])), None)
    if dropdown:
        sample = dropdown["extra"][0]
        lines.append(f'  wt taiga update-userstory --ref <REF> --custom-attrs "{dropdown["id"]}::{sample}"')

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_custom_attributes())
