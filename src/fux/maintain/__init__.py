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


def cmd_daemon(args) -> int:
    """`fux daemon start | stop | status` — the URL freshness clock.

    `--serve` is the child's entry point and is hidden: it runs the loop in this
    process and returns only when stopped. Nobody types it, and documenting it
    would invite wiring the loop into a supervisor — the global install this
    verb exists to avoid (Arpit, 2026-08-27: *"the code only lives inside the
    project, not globally"*).
    """
    from . import daemon as daemon_mod

    root = _root()

    if getattr(args, "serve", False):
        daemon_mod.serve(root)
        return 0

    action = getattr(args, "action", "status") or "status"

    if action == "start":
        outcome = daemon_mod.start(root)
        if outcome == "already-running":
            state = daemon_mod.status(root)
            print(f"daemon: already running (pid {state['pid']})")
            return 0
        print(
            f"daemon: started — sweeping every {daemon_mod.sweep_minutes(root)} min.\n"
            "  It runs until you stop it: `fux daemon stop`.\n"
            "  Nothing was installed outside this repository."
        )
        return 0

    if action == "stop":
        outcome = daemon_mod.stop(root)
        if outcome == "not-running":
            print("daemon: not running")
            return 0
        if outcome == "timeout":
            # Deliberately not escalated to a kill: a daemon slow to stop is
            # usually mid-`write_index`, which is when killing it costs a
            # partial shard.
            print(
                "daemon: asked to stop and it has not exited yet. It finishes the "
                "unit of work it is in, then goes.\n"
                "  `fux daemon status` to check; fux will not kill it."
            )
            return 1
        print("daemon: stopped")
        return 0

    state = daemon_mod.status(root)
    if getattr(args, "json", False):
        print(json.dumps(state, indent=2, sort_keys=True))
        return 0
    if state["running"]:
        print(f"  daemon    running (pid {state['pid']})")
    else:
        print("  daemon    not running")
    print(f"  sweep     every {daemon_mod.sweep_minutes(root)} min")
    last = state.get("last")
    print(f"  last pass {last['outcome'] if last else 'none yet'}")
    return 0


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
