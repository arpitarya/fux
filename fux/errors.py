"""The one typed error for fux (plan §error-handling contract).

`FuxError` carries a clear, user-facing message for an *expected* failure (unknown
rule id, missing `.fux/`, bad arg, unreadable file in a read command). The CLI
top-level guard (`fux/cli.py` `main`) renders it as a terse `error: <msg>` + exit 1,
never a raw traceback. There is deliberately **no** subclass hierarchy — one thin
class, no ceremony. Unexpected exceptions stay unexpected (traceback under
`FUX_DEBUG`); only obviously-user-facing failures raise this.
"""
from __future__ import annotations


class FuxError(Exception):
    """An expected, user-facing failure — rendered as `error: <msg>`, exit 1."""
