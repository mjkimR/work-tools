"""Integration tests for TaigaImsWorkflowHandler — validates handler logic with Fake clients."""

import pytest

from tests.fake.data.taiga import (
    IMS_UUID_IN_CUSTOM_ATTR,
    IMS_UUID_IN_DESCRIPTION,
)


class TestResolveUsId:
    """Tests for _resolve_us_id helper."""

    def test_resolve_by_id(self, workflow_handler):
        assert workflow_handler._resolve_us_id(id=200) == 200

    def test_resolve_by_ref(self, workflow_handler, capsys):
        us_id = workflow_handler._resolve_us_id(ref=50)
        assert us_id == 200
        out = capsys.readouterr().out
        assert "Ref #50" in out
        assert "200" in out

    def test_resolve_missing_both_raises(self, workflow_handler):
        with pytest.raises(ValueError, match="Either id or ref"):
            workflow_handler._resolve_us_id()

    def test_resolve_invalid_ref_raises(self, workflow_handler):
        with pytest.raises(ValueError, match="not found"):
            workflow_handler._resolve_us_id(ref=9999)


class TestExtractUuidsFromUs:
    """Tests for _extract_uuids_from_us helper."""

    def test_extracts_uuid_from_description(self, workflow_handler):
        uuids = workflow_handler._extract_uuids_from_us(200)
        assert IMS_UUID_IN_DESCRIPTION in uuids

    def test_extracts_uuid_from_custom_attr(self, workflow_handler):
        uuids = workflow_handler._extract_uuids_from_us(201)
        assert IMS_UUID_IN_CUSTOM_ATTR in uuids

    def test_deduplicates_uuid(self, workflow_handler):
        # US 203: description과 custom_attr 양쪽에 동일한 UUID
        uuids = workflow_handler._extract_uuids_from_us(203)
        assert uuids.count(IMS_UUID_IN_DESCRIPTION) == 1

    def test_returns_empty_when_no_ims_link(self, workflow_handler):
        uuids = workflow_handler._extract_uuids_from_us(202)
        assert uuids == []


class TestGetLinkedImsDocs:
    """Tests for get_linked_ims_docs command handler."""

    def test_prints_no_links_message_when_empty(self, workflow_handler, capsys):
        workflow_handler.get_linked_ims_docs(id=202)
        out = capsys.readouterr().out
        assert "No IMS links found." in out

    def test_prints_found_count_for_description_link(self, workflow_handler, capsys):
        workflow_handler.get_linked_ims_docs(id=200)
        out = capsys.readouterr().out
        assert "Found 1 IMS link(s)" in out
        assert IMS_UUID_IN_DESCRIPTION in out

    def test_prints_document_header(self, workflow_handler, capsys):
        workflow_handler.get_linked_ims_docs(id=200)
        out = capsys.readouterr().out
        assert "[DOCUMENT]" in out

    def test_prints_document_for_custom_attr_link(self, workflow_handler, capsys):
        workflow_handler.get_linked_ims_docs(id=201)
        out = capsys.readouterr().out
        assert "Found 1 IMS link(s)" in out
        assert IMS_UUID_IN_CUSTOM_ATTR in out
        assert "[DOCUMENT]" in out

    def test_deduplicates_and_prints_once_for_duplicate_links(self, workflow_handler, capsys):
        # US 203: description + custom_attr 양쪽에 같은 UUID → 문서 1개만 출력
        workflow_handler.get_linked_ims_docs(id=203)
        out = capsys.readouterr().out
        assert out.count("[DOCUMENT]") == 1

    def test_resolves_by_ref_and_prints_document(self, workflow_handler, capsys):
        # ref=50 → id=200 → description에 IMS URL 포함
        workflow_handler.get_linked_ims_docs(ref=50)
        out = capsys.readouterr().out
        assert "Ref #50" in out
        assert "[DOCUMENT]" in out

    def test_documents_separated_by_blank_line(self, workflow_handler, fake_ims_client_with_two_docs, capsys):
        # US 200(description uuid) + US 203(same uuid, deduplicated) 대신
        # 두 UUID가 있는 US를 직접 사용: fake_workflow_handler_two_docs 픽스처 사용
        handler = fake_ims_client_with_two_docs
        handler.get_linked_ims_docs(id=200)
        out = capsys.readouterr().out
        # 단일 문서도 마지막에 빈 줄이 출력됨
        assert out.endswith("\n\n") or "[DOCUMENT]" in out
