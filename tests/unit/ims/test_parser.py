"""Tests for ImsDocumentParser — HTML fixture-based parsing verification."""

import pytest
from modules.ims.parser import ImsDocumentParser


@pytest.fixture
def parser():
    return ImsDocumentParser()


class TestParseDocument:
    """Full document parsing from sample HTML."""

    def test_uid(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert doc.uid == "8226"

    def test_title_and_project(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert doc.title == "Implement user authentication"
        assert doc.project == "ProjectAlpha"

    def test_author_and_date(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert doc.author == "홍길동"
        assert doc.created_at == "2025-06-15"
        assert doc.view_count == "128"

    def test_ext_fields(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert doc.attrs["Category"] == "Feature"
        assert doc.attrs["Status"] == "In Progress"
        assert doc.attrs["Assignee"] == "홍길동"

    def test_content(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert "main content" in doc.content_text
        assert "multiple paragraphs" in doc.content_text
        assert "<p>" in doc.content_html

    def test_attachments(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert len(doc.attachments) == 2
        assert doc.attachments[0].filename == "spec.pdf"
        assert doc.attachments[0].size == "2.1MB"
        assert doc.attachments[0].download_url == "/download/spec.pdf"
        assert doc.attachments[1].filename == "design.png"

    def test_comments(self, parser, sample_document_html):
        doc = parser.parse(sample_document_html)
        assert len(doc.comments) == 2
        assert doc.comments[0].author == "김철수"
        assert doc.comments[0].content == "Looks good, approved."
        assert doc.comments[1].author == "박영희"
        assert doc.comments[1].date == "2025-06-17"


class TestParseEdgeCases:
    """Edge case handling."""

    def test_login_required_raises(self, parser, login_required_html):
        with pytest.raises(ValueError, match="kboard-document-wrap not found"):
            parser.parse(login_required_html)
