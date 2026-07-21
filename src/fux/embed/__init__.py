"""Bundled static-embedding runtime (stdlib-only; see model.py, store.py)."""

from .model import MAX_TOKENS, Model, Vec, get_model

__all__ = ["MAX_TOKENS", "Model", "Vec", "get_model"]
