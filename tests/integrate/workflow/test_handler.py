"""Integration tests for UserStoryHandler — validates full context retrieval output."""

import pytest


class TestGetFullContext:
    """Tests for get_full_context handler."""

    def test_prints_user_story_details(self, workflow_handler, capsys):
        # US #42 (ID 100)
        workflow_handler.get_full_context("42")
        out = capsys.readouterr().out
        assert "[User Story] #42 - Implement login feature" in out
        assert "Status   : New" in out
        assert "Assignee : Test User" in out
        assert "URL      : https://tree.taiga.io/project/test-project/us/42" in out

    def test_prints_custom_attributes(self, workflow_handler, capsys):
        workflow_handler.get_full_context("42")
        out = capsys.readouterr().out
        assert "[Custom Attributes]" in out
        assert "Priority: High" in out
        assert "Sprint-Goal: Complete login flow" in out

    def test_prints_linked_tasks(self, workflow_handler, capsys):
        workflow_handler.get_full_context("42")
        out = capsys.readouterr().out
        assert "[Tasks] (1 total)" in out
        assert "- #501 [In Progress] Task 1 for US 100 (Assignee: Test User)" in out

    def test_prints_comments(self, workflow_handler, capsys):
        workflow_handler.get_full_context("42")
        out = capsys.readouterr().out
        assert "[Comments] (1 total)" in out
        assert "[2025-06-20 10:00] Alice:" in out
        assert "    Initial comment for US 100" in out

    def test_extracts_ims_from_description(self, workflow_handler, capsys):
        # US #50 (ID 200) has IMS link in description (uid=8226)
        workflow_handler.get_full_context("50")
        out = capsys.readouterr().out
        assert "[IMS Documents] (1 linked)" in out
        assert "uid     : 8226" in out

    def test_extracts_ims_from_custom_attributes(self, workflow_handler, fake_ims_client, capsys):
        # US #51 (ID 201) has IMS link in custom attr (uid=8227)
        from tests.fake.data.ims import SAMPLE_DOCUMENT_HTML

        html_8227 = SAMPLE_DOCUMENT_HTML.replace('value="8226"', 'value="8227"')
        fake_ims_client.add_document("8227", html_8227)

        workflow_handler.get_full_context("51")
        out = capsys.readouterr().out
        assert "[IMS Documents] (1 linked)" in out
        assert "uid     : 8227" in out

    def test_extracts_multiple_different_ims_documents(
        self, workflow_handler, fake_taiga_client_with_ims, fake_ims_client, capsys
    ):
        # Scenario: Both description (8226) and custom attributes (8228) have different IMS links
        from tests.fake.data.ims import SAMPLE_DOCUMENT_HTML
        from tests.fake.data.taiga import IMS_FAKE_BASE_URL

        # 1. Prepare Taiga data
        us_id = 205
        fake_taiga_client_with_ims.created_stories.append(
            {
                "id": us_id,
                "ref": 55,
                "subject": "Multiple IMS test",
                "description": f"Link 1: {IMS_FAKE_BASE_URL}/?uid=8226",
                "project_extra_info": {"slug": "test"},
                "status_extra_info": {"name": "New"},
            }
        )

        # Manually update lookup tables as they are mutable in the fake data module
        from tests.fake.data.taiga import CUSTOM_ATTRIBUTE_VALUES_WITH_IMS, USER_STORY_BY_REF

        USER_STORY_BY_REF[55] = fake_taiga_client_with_ims.created_stories[-1]
        CUSTOM_ATTRIBUTE_VALUES_WITH_IMS[us_id] = {
            "version": 1,
            "attributes_values": {"2": f"Link 2: {IMS_FAKE_BASE_URL}/?uid=8228"},
        }

        # 2. Prepare IMS data (8228)
        html_8228 = SAMPLE_DOCUMENT_HTML.replace('value="8226"', 'value="8228"')
        fake_ims_client.add_document("8228", html_8228)

        # 3. Execute
        workflow_handler.get_full_context("55")
        out = capsys.readouterr().out

        # 4. Verify: Both documents should be retrieved and printed
        assert "[IMS Documents] (2 linked)" in out
        assert "uid     : 8226" in out
        assert "uid     : 8228" in out

    def test_handles_no_ims_links(self, workflow_handler, capsys):
        # US #52 (ID 202) has no IMS links
        workflow_handler.get_full_context("52")
        out = capsys.readouterr().out
        assert "[IMS Documents] (0 linked)" in out
        assert "(none)" in out

    def test_deduplicates_ims_links(self, workflow_handler, capsys):
        # US #53 (ID 203) has same IMS link in both description and custom attr
        workflow_handler.get_full_context("53")
        out = capsys.readouterr().out
        assert "[IMS Documents] (1 linked)" in out

    def test_invalid_ref_raises(self, workflow_handler):
        with pytest.raises(ValueError, match="not found"):
            workflow_handler.get_full_context("999")
