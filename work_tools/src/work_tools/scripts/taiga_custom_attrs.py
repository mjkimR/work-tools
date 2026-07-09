"""
taiga_custom_attrs.py
---------------------
Dynamic generator for docs_manifest.yaml.

Fetches the list of custom attributes defined in the Taiga project and
returns a formatted Markdown section suitable for AI context injection.

Usage (docs_manifest.yaml):
    generators:
      - "work_tools.scripts.taiga_custom_attrs:generate_custom_attributes"
"""

from work_tools.core import setup
from work_tools.modules.taiga.client import TaigaClient


def generate_custom_attributes() -> str:
    """Fetch Taiga custom attributes and return a formatted Markdown string.

    Returns:
        A Markdown section listing each custom attribute's ID, name, and type, plus the
        allowed values of every ``dropdown`` attribute and usage examples derived from them.
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

    # Derive every example from the live attribute list. Hardcoding an ID here would
    # silently start pointing at a deleted or renamed attribute.
    examples = []

    plain = next((a for a in attrs if a.get("type") != "dropdown"), None)
    if plain:
        examples.append(f'  wt taiga update-userstory --ref <REF> --custom-attrs "{plain["id"]}::<{plain["name"]} value>"')

    dropdown = next((a for a in attrs if a.get("type") == "dropdown" and (a.get("extra") or [])), None)
    if dropdown:
        sample = dropdown["extra"][0]
        examples.append(f'  wt taiga update-userstory --ref <REF> --custom-attrs "{dropdown["id"]}::{sample}"')

    if examples:
        lines += ["", "Example:", *examples]

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_custom_attributes())
