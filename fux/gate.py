"""`fux gate` — the CI / pre-commit enforcement surface ($0).

The Stop hook catches drift only inside a Claude session; `gate` is the
out-of-session backstop: rebuild the views, then fail (exit 2) on blocking `check`
findings or failed `verify` invariants. Lint is advisory unless `--strict-lint`.
`--install` drops a git pre-commit hook that runs it.
"""
from __future__ import annotations

import stat
from pathlib import Path

from fux import build, check, gitutil, lint, verify
from fux.findings import blocking

_PRECOMMIT = """#!/bin/sh
# Fux gate — keep documented knowledge in sync with code. Installed by `fux gate --install`.
if command -v fux >/dev/null 2>&1; then FUX="fux"; else
  PY="$(command -v python3.14 || command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)"
  FUX="$PY -m fux"
fi
exec $FUX gate
"""


def run(root: Path, strict_lint: bool = False) -> tuple[int, str]:
    """Return (exit_code, report). 0 = pass, 2 = blocked."""
    build.run(root)                                   # views current before judging
    findings = check.run(root)
    blockers = blocking(findings)
    vres = verify.run(root)
    vfail = [v for v in vres if v.status == "fail"]
    lints = lint.run(root)

    lines = ["fux gate", ""]
    lines.append(f"  check:   {len(findings)} finding(s), {len(blockers)} blocking")
    for f in blockers:
        lines.append(f"    ✗ {f.line()}")
    vpass = sum(v.status == "pass" for v in vres)
    lines.append(f"  verify:  {vpass} pass, {len(vfail)} fail, "
                 f"{sum(v.status == 'skip' for v in vres)} skip")
    for v in vfail:
        lines.append(f"    ✗ {v.rule_id} {v.detail}".rstrip())
    lines.append(f"  lint:    {len(lints)} advisory finding(s)"
                 f"{' (enforced)' if strict_lint else ''}")
    for f in lints[:10]:
        lines.append(f"    · {f.line()}")

    failed = bool(blockers) or bool(vfail) or (strict_lint and bool(lints))
    lines.append("")
    lines.append("✗ gate failed — resolve the blocking findings above." if failed
                 else "✔ gate passed — knowledge is in sync with code.")
    return (2 if failed else 0, "\n".join(lines))


def install_precommit(root: Path) -> Path:
    """Write a git pre-commit hook that runs `fux gate`. Returns the hook path."""
    hooks = gitutil.hooks_dir(root)
    if hooks is None:
        raise SystemExit("fux: not a git repo (no hooks dir) — run `git init` first.")
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-commit"
    hook.write_text(_PRECOMMIT, encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hook
