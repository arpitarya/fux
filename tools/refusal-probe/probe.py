#!/usr/bin/env python3
"""Run a repo's refusal rules against a CAPTURED response, and say what happens.

This is [ADR-REFUSAL](../../docs/adr/0051_refusals.md)'s veto check made
runnable, and it is the tool a consumer uses to debug a rule. The record's veto
condition is *"a refusal is captured that no byte-pure condition can express"* —
and the only way to evaluate that is to hold the real bytes and ask.

⚠ **It never fetches.** A capture is a file on disk, saved by whatever got it
(a browser's "save page as", `Fetch.getResponseBody`, a fetcher writing its
input out). Fetching here would make the tool's answer depend on a session,
which is the whole reason refusals exist.

    python3 tools/refusal-probe/probe.py <repo-root> <case-file>

The case file is TOML, one `[[case]]` per captured response:

    [[case]]
    label        = "the real Office web viewer"
    url          = "https://1drv.ms/x/c/DRIVE/TOKEN?e=PtMf2M"
    content_type = "text/html; charset=utf-8"
    body         = "captures/viewer-shell.html"     # relative to the case file
    expect       = "refused"                        # or "accepted"; optional

`expect` turns the probe into an assertion: any case whose outcome disagrees
makes the process exit 1. A capture with `expect = "accepted"` is worth more
than one with `expect = "refused"` — it is what catches an over-broad rule,
which is the failure decision 8's strictness cannot see.
"""

from __future__ import annotations

import sys
import textwrap
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.errors import FuxError  # noqa: E402
from fux.ingest import refusals  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print(f"usage: {Path(argv[0]).name} <repo-root> <case-file>", file=sys.stderr)
        return 2

    root, case_file = Path(argv[1]), Path(argv[2])
    try:
        rules = refusals.load(root)
    except FuxError as exc:
        print(f"rules: {exc}", file=sys.stderr)
        return 2

    print(f"rules loaded: {len(rules)}")
    for rule in rules:
        print(f"  {rule.name}")
    print()

    cases = tomllib.loads(case_file.read_text(encoding="utf-8")).get("case", [])
    failures = 0
    for case in cases:
        raw = (case_file.parent / case["body"]).read_bytes()
        why = refusals.refused(rules, case["url"], case["content_type"], raw)
        outcome = "refused" if why else "accepted"
        expect = case.get("expect")
        bad = expect is not None and expect != outcome
        failures += bad

        print(f"{outcome.upper():8}  {case['label']}{'   << expected ' + expect if bad else ''}")
        print(f"          {len(raw):,} bytes, {case['content_type'].split(';')[0]}")
        for line in textwrap.wrap(why, 68) if why else ():
            print(f"          {line}")
        print()

    if failures:
        print(f"{failures} case(s) did not match `expect` — the rules changed meaning.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
