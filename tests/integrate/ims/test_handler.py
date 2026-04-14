"""Integration tests for ImsCLIHandlers — validates handler output with FakeImsClient."""

import pytest


class TestGetDocument:
    """Tests for get_document handler."""

    def test_prints_document_header(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "[DOCUMENT]" in out

    def test_prints_uid(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "uid     : 8226" in out

    def test_prints_title(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "Implement user authentication" in out

    def test_prints_project(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "ProjectAlpha" in out

    def test_prints_author_and_date(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "홍길동" in out
        assert "2025-06-15" in out

    def test_prints_attributes_section(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "[ATTRIBUTES]" in out
        assert "Category" in out
        assert "Feature" in out

    def test_prints_content_section(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "[CONTENT]" in out
        assert "main content" in out

    def test_prints_attachments_section(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "[ATTACHMENTS]" in out
        assert "spec.pdf" in out

    def test_prints_comments_section(self, ims_handlers, capsys):
        ims_handlers.get_document("8226")
        out = capsys.readouterr().out
        assert "[COMMENTS]" in out
        assert "김철수" in out
        assert "Looks good, approved." in out

    def test_unknown_uid_raises(self, ims_handlers):
        with pytest.raises(ValueError, match="not found"):
            ims_handlers.get_document("9999")


class TestGetDocuments:
    """Tests for get_documents handler."""

    def test_prints_all_documents(self, ims_handlers, fake_ims_client, capsys):
        fake_ims_client.add_document("8227", fake_ims_client._documents["8226"])
        ims_handlers.get_documents(["8226", "8227"])
        out = capsys.readouterr().out
        assert out.count("[DOCUMENT]") == 2

    def test_documents_separated_by_blank_line(self, ims_handlers, fake_ims_client, capsys):
        fake_ims_client.add_document("8227", fake_ims_client._documents["8226"])
        ims_handlers.get_documents(["8226", "8227"])
        out = capsys.readouterr().out
        # 각 문서 사이에 빈 줄이 있어야 함
        assert "\n\n" in out

    def test_single_uid_in_list(self, ims_handlers, capsys):
        ims_handlers.get_documents(["8226"])
        out = capsys.readouterr().out
        assert "[DOCUMENT]" in out
        assert "8226" in out

    def test_unknown_uid_in_list_raises(self, ims_handlers):
        with pytest.raises(ValueError, match="not found"):
            ims_handlers.get_documents(["8226", "0000"])
