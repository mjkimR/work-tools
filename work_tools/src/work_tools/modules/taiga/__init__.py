"""
taiga
-----
CLI tool for in-house Taiga project management integration.
Supports creating and updating user stories and tasks, querying project data,
and managing statuses and custom attributes via the Taiga REST API.
"""

from .api import cli
from .client import TaigaClient

__all__ = [
    "cli",
    "TaigaClient",
]
