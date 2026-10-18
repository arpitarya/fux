"""Fux — a search index for your written knowledge, committed to git.

The index holds statistics, never content: documents stay in the systems
that own them, and are fetched and verified at answer time. The laws that
bind this — cost, determinism, network, content — are stated once each in
`records/0001_LAWS.md` and nowhere else.

`from fux import open` is the read API (SR-API); the CLI is `fux`.
"""

__version__ = "4.0.3"

__all__ = ["__version__", "open"]


def __getattr__(name: str):
    """`fux.open` — the frozen read surface (SR-API), imported on first use.

    Lazy, and guarded, because this file is the core layer's (W-282): every
    `fux.*` module runs it, and the writer must import without the reader.
    `from fux import open` works exactly as before wherever the reader is
    installed — `fux-engine` always — and names the package to install where
    it is not.
    """
    if name == "open":
        try:
            from .api import open as read_api
        except ImportError:  # a writer-only install: the read API is fux-reader's
            raise ImportError(
                "`fux.open` is the read API, and it ships in fux-reader — "
                "install fux-engine or fux-reader"
            ) from None
        return read_api
    raise AttributeError(f"module 'fux' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals(), "open"})
