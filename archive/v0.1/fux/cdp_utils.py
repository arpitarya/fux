"""Resolve the Chrome DevTools Protocol endpoint for the ingest skill's render
escalation (handoff §B). Precedence: ``--cdp-port``/``--cdp-host`` flags →
``FUX_CDP_PORT``/``FUX_CDP_HOST`` env → ``cdp_port``/``cdp_host`` in config →
default ``127.0.0.1:9299``.

Pure resolution — no socket, no network. The skill (host agent) does the actual
CDP connection with its own tokens; the engine only computes the endpoint string.
"""
from __future__ import annotations

import os

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9299


def _coerce_port(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve(cfg: dict | None = None, host_flag: str | None = None,
            port_flag: int | str | None = None) -> tuple[str, int]:
    """Return the resolved ``(host, port)`` by the documented precedence."""
    cfg = cfg or {}
    host = (host_flag
            or os.environ.get("FUX_CDP_HOST")
            or cfg.get("cdp_host")
            or DEFAULT_HOST)
    port = (_coerce_port(port_flag)
            if port_flag is not None else None)
    if port is None:
        port = _coerce_port(os.environ.get("FUX_CDP_PORT"))
    if port is None:
        port = _coerce_port(cfg.get("cdp_port"))
    if port is None:
        port = DEFAULT_PORT
    return str(host), port


def endpoint(cfg: dict | None = None, host_flag: str | None = None,
             port_flag: int | str | None = None) -> str:
    """The ``http://host:port`` base URL for the CDP JSON endpoint."""
    host, port = resolve(cfg, host_flag, port_flag)
    return f"http://{host}:{port}"
