import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).parent


@pytest.fixture
def sample_document_html():
    return (FIXTURES / "sample_document.html").read_text(encoding="utf-8")


@pytest.fixture
def login_required_html():
    return (FIXTURES / "login_required.html").read_text(encoding="utf-8")
