"""Tests for the dynamic custom-attributes doc generator.

The generated section is injected into `wt docs read-docs task-writer`, so it is the
only place an AI agent learns real attribute IDs and dropdown options. Every example it
emits must be derived from the live attribute list — a hardcoded ID would silently rot
into a reference to a deleted attribute.
"""

from unittest.mock import MagicMock, patch

from work_tools.scripts.taiga_custom_attrs import generate_custom_attributes

from tests.fake.data.taiga import CUSTOM_ATTRIBUTES


def _generate(attrs):
    """Run the generator against a fixed attribute list, bypassing setup/HTTP."""
    client = MagicMock()
    client.get_userstory_custom_attributes.return_value = attrs
    with (
        patch("work_tools.scripts.taiga_custom_attrs.setup"),
        patch("work_tools.scripts.taiga_custom_attrs.TaigaClient", return_value=client),
    ):
        return generate_custom_attributes()


class TestGenerateCustomAttributes:
    """Validate the Markdown emitted for AI context injection."""

    def test_lists_every_attribute_with_id_and_type(self):
        out = _generate(CUSTOM_ATTRIBUTES)
        assert "- Priority (ID: 1, type: text)" in out
        assert "- Target Group (ID: 15, type: dropdown)" in out

    def test_dropdown_options_are_exposed(self):
        # Without these, an agent cannot know which values the handler will accept.
        out = _generate(CUSTOM_ATTRIBUTES)
        assert "Allowed values (choose exactly one): 고객사_A | 고객사_B | 내부" in out

    def test_examples_are_derived_from_the_attribute_list(self):
        out = _generate(CUSTOM_ATTRIBUTES)
        # First non-dropdown attribute drives the generic example...
        assert '--custom-attrs "1::<Priority value>"' in out
        # ...and the first dropdown option drives the dropdown example.
        assert '--custom-attrs "15::고객사_A"' in out

    def test_no_example_references_an_absent_attribute(self):
        # Regression guard: the generic example used to hardcode ID 8, which is absent here.
        out = _generate(CUSTOM_ATTRIBUTES)
        defined = {str(a["id"]) for a in CUSTOM_ATTRIBUTES}

        cited = set()
        for line in out.splitlines():
            if '--custom-attrs "' not in line or "<ATTR_ID>" in line:
                continue  # skip the prose template, which is deliberately a placeholder
            cited.add(line.split('--custom-attrs "')[1].split("::")[0])

        assert cited, "expected at least one concrete example"
        assert cited <= defined

    def test_empty_attribute_list_returns_placeholder(self):
        assert _generate([]) == "_No custom attributes defined for this project._"

    def test_dropdown_without_options_emits_no_example(self):
        # An optionless dropdown yields nothing to demonstrate, so the header is omitted
        # rather than dangling over an empty list.
        out = _generate([{"id": 3, "name": "Empty", "type": "dropdown", "extra": []}])
        assert "- Empty (ID: 3, type: dropdown)" in out
        assert "Allowed values" not in out
        assert "Example:" not in out
