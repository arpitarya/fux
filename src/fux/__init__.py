"""Fux — a search index for your written knowledge, committed to git.

The index holds statistics, never content: documents stay in the systems
that own them, and are fetched and verified at answer time. The laws that
bind this — cost, determinism, network, content — are stated once each in
`records/0001_LAWS.md` and nowhere else.

`from fux import open` is the read API (SR-API); the CLI is `fux`.
"""

__version__ = "3.0.0-alpha.3"

from .api import open  # noqa: A004,E402  (SR-API — the frozen read surface)

__all__ = ["__version__", "open"]
