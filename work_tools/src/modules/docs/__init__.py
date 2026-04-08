"""
docs
----
Provides the read-docs CLI tool.
Composes contextual information for a given subject by aggregating reference documents,
environment variables, and dynamically generated data — designed for AI consumption.
"""

from .api import cli
from .loader import DocsLoader

__all__ = [
    "cli",
    "DocsLoader",
]

