"""IMS (WordPress/KBoard) HTML parser module.

Flow:
    1. Acquire session using cookies copied from browser (or auto-login)
    2. Fetch HTML via GET /?uid={uid}&mod=document
    3. Extract required fields using this parser
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag


@dataclass
class ImsAttachment:
    filename: str
    size: str
    download_url: str


@dataclass
class ImsComment:
    author: str
    date: str
    content: str


@dataclass
class ImsDocument:
    uid: str
    title: str
    project: str  # [ProjectName] part extracted from the title
    author: str
    created_at: str
    view_count: str

    # ext-field-option fields (variable fields such as category/status/assignee)
    attrs: dict[str, str] = field(default_factory=dict)

    content_html: str = ""
    content_text: str = ""

    attachments: list[ImsAttachment] = field(default_factory=list)
    comments: list[ImsComment] = field(default_factory=list)


class ImsDocumentParser:
    """KBoard document detail page HTML parser."""

    def parse(self, html: str) -> ImsDocument:
        soup = BeautifulSoup(html, "html.parser")

        wrap = soup.select_one("#kboard-document .kboard-document-wrap")
        if wrap is None:
            raise ValueError("kboard-document-wrap not found. The page may require login.")
        uid = self._parse_uid(soup)
        title, project = self._parse_title(wrap)
        author, created_at, view_count = self._parse_summary(wrap)
        attrs = self._parse_ext_fields(wrap)
        content_html, content_text = self._parse_content(wrap)
        attachments = self._parse_attachments(wrap)
        comments = self._parse_comments(soup)

        return ImsDocument(
            uid=uid,
            title=title,
            project=project,
            author=author,
            created_at=created_at,
            view_count=view_count,
            attrs=attrs,
            content_html=content_html,
            content_text=content_text,
            attachments=attachments,
            comments=comments,
        )

    def _parse_uid(self, soup: BeautifulSoup) -> str:
        """Extract uid from hidden input #content-uid or URL canonical."""
        el = soup.select_one("#content-uid")
        if el:
            return str(el.get("value", ""))

        canonical = soup.select_one("link[rel='canonical']")
        if canonical:
            href = str(canonical.get("href", ""))
            # /?kboard_content_redirect=8226 or /?uid=8226
            for param in ("kboard_content_redirect=", "uid="):
                if param in href:
                    return href.split(param)[-1].split("&")[0]

        return ""

    def _parse_title(self, wrap: Tag) -> tuple[str, str]:
        """Separate title and [ProjectName]."""
        h1 = wrap.select_one(".kboard-title h1")
        if h1 is None:
            return "", ""

        raw = h1.get_text(separator=" ", strip=True)

        # "[ProjectName] Title" pattern
        project = ""
        title = raw
        if raw.startswith("["):
            end = raw.find("]")
            if end != -1:
                project = raw[1:end].strip()
                title = raw[end + 1 :].strip()

        return title, project

    def _parse_summary(self, wrap: Tag) -> tuple[str, str, str]:
        """Parse author / created date / view count."""
        author = wrap.select_one(".detail-writer .detail-value")
        date = wrap.select_one(".detail-date .detail-value")
        view = wrap.select_one(".detail-view .detail-value")

        return (
            author.get_text(strip=True) if author else "",
            date.get_text(strip=True) if date else "",
            view.get_text(strip=True) if view else "",
        )

    def _parse_ext_fields(self, wrap: Tag) -> dict[str, str]:
        """Parse ext-field-option rows such as category/status/assignee/version."""
        attrs: dict[str, str] = {}
        for row in wrap.select(".ext-field-option .row"):
            key_el = row.select_one(".column")
            # value is in .text or .preview > pre
            val_el = row.select_one(".text") or row.select_one(".preview pre")
            if key_el and val_el:
                key = key_el.get_text(strip=True)
                val = val_el.get_text(strip=True)
                attrs[key] = val
        return attrs

    def _parse_content(self, wrap: Tag) -> tuple[str, str]:
        """Return content HTML and plain text."""
        content_div = wrap.select_one(".kboard-content .content-view")
        if content_div is None:
            return "", ""
        return str(content_div), content_div.get_text(separator="\n", strip=True)

    def _parse_attachments(self, wrap: Tag) -> list[ImsAttachment]:
        attachments = []
        for li in wrap.select(".kboard-detail-attach .detail-attach"):
            a = li.select_one("a.attach-link")
            filename_el = li.select_one(".filename")
            size_el = li.select_one(".size")
            if a and filename_el:
                attachments.append(
                    ImsAttachment(
                        filename=filename_el.get_text(strip=True),
                        size=size_el.get_text(strip=True) if size_el else "",
                        download_url=str(a.get("href", "")),
                    )
                )
        return attachments

    def _parse_comments(self, soup: BeautifulSoup) -> list[ImsComment]:
        """Parse comment list (kboard-comments-area)."""
        comments = []
        # Actual HTML: .kboard-comments-default ul li.kboard-comments-item
        for item in soup.select(".kboard-comments-default li.kboard-comments-item"):
            author_el = item.select_one(".comments-list-username")
            date_el = item.select_one(".comments-list-create")
            content_el = item.select_one(".comments-list-content")
            comments.append(
                ImsComment(
                    author=author_el.get_text(strip=True) if author_el else "",
                    date=date_el.get_text(strip=True) if date_el else "",
                    content=content_el.get_text(separator="\n", strip=True) if content_el else "",
                )
            )
        return comments
