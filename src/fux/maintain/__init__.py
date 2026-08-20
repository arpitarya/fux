"""The maintenance plane — M5. Hooks, the merge driver, and L5 at write time.

Three pieces that together make the index maintain itself in a real repository:

| piece | where | what it stops |
|---|---|---|
| git hooks | `hooks.py` | an index that silently drifts from the content it describes |
| the merge driver | `mergedriver.py` | two people working at once producing a textual conflict in a machine plane |
| **L5 at write time** | `store/writer.py` | a private document's title reaching a committed file |

The third one is not in this package deliberately: it belongs in the writer,
because the point of moving it there is that **no path into a committed shard
can skip it**. A check that lives beside the thing it guards is a check; one
that lives in a plane you have to remember to call is a convention.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import find_root
from ..errors import FuxError
from . import hooks as hooks_mod

__all__ = ["cmd_hooks"]


def _root() -> Path:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")
    return root


def cmd_hooks(args) -> int:
    """`fux hooks` — install, inspect or remove the maintenance wiring."""
    root = _root()

    if getattr(args, "uninstall", False):
        report = hooks_mod.uninstall(root)
        for name in report.installed:
            print(f"  removed {name}")
        for name in report.refused:
            print(f"  kept    {name} (not written by fux — yours)")
        print("hooks: the merge driver is unregistered; `.gitattributes` is left alone")
        return 0

    if getattr(args, "json", False) or getattr(args, "status", False):
        state = hooks_mod.status(root)
        if getattr(args, "json", False):
            print(json.dumps(state, indent=2, sort_keys=True))
        else:
            for name, how in sorted(state["hooks"].items()):
                print(f"  {name:<14} {how}")
            print(f"  merge driver   {state['merge_driver']}")
            print(f"  .gitattributes {'wired' if state['gitattributes'] else 'not wired'}")
        return 0

    report = hooks_mod.install(root)
    for name in report.installed:
        print(f"  wrote  {name}")
    for name in report.kept:
        print(f"  kept   {name} (already current)")
    for name in report.refused:
        # Refusing is the whole policy: silently replacing a repo's own hook is
        # how a team loses their tooling to a tool they installed to help.
        print(f"  REFUSED {name} — a hook is already there and fux did not write it")
    print(f"  merge driver registered: {report.merge_driver}")
    if report.refused:
        print(
            "\nhooks: some were refused. Move or delete them and re-run, or chain "
            "`fux ingest` from your own hook."
        )
    return 0
