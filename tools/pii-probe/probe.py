#!/usr/bin/env python3
"""Show what a PII rule would remove from your corpus, BEFORE you commit to it.

Redaction is irreversible in the index, and the dangerous failure is not a
broken regex -- `fux doctor` catches those. It is a rule that is well-formed
and **too broad**: it removes real vocabulary, documents stop being findable by
the words that would have found them, and nothing anywhere looks wrong.

This is the only thing in the repo that makes that visible. Read what a rule
caught before you enable it.

    python3 tools/pii-probe/probe.py <repo-root> [--rule NAME] [--context N]
                                                 [--max N] [--counts-only]

⚠ **It prints the values it found.** That is the point -- you cannot judge a
rule without seeing what it caught -- but it means the output is as sensitive
as the corpus. Do not paste it into a ticket.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.errors import FuxError  # noqa: E402
from fux.ingest import pii  # noqa: E402


def _documents(root: Path):
    """Every indexed document's text, `file:` and `url:` alike.

    Reads through `enrich._document_text`, which is the one function that
    already knows a `url:` document lives in `.fux/acquired/`. A second reader
    here would drift from it.
    """
    from fux import store as store_mod
    from fux.enrich import _document_text

    for record in store_mod.read_index(root).values():
        text = _document_text(root, record)
        if text:
            yield record.get("loc", record.get("id", "?")), text


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pii-probe", description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--rule", help="only this rule (default: every rule)")
    ap.add_argument("--context", type=int, default=32, help="chars either side")
    ap.add_argument("--max", type=int, default=8, help="examples per rule")
    ap.add_argument("--counts-only", action="store_true", help="no values, just counts")
    args = ap.parse_args(argv[1:])

    try:
        rules = pii.load(args.root)
    except FuxError as exc:
        print(f"pii rules: {exc}", file=sys.stderr)
        return 2
    if args.rule:
        rules = tuple(r for r in rules if r.name == args.rule)
        if not rules:
            print(f"no rule named {args.rule!r}", file=sys.stderr)
            return 2
    if not rules:
        print("no rules in .fux/pii.toml — nothing to probe")
        return 0

    counts: Counter[str] = Counter()
    docs: Counter[str] = Counter()
    examples: dict[str, list[str]] = {r.name: [] for r in rules}
    total_docs = 0

    for loc, text in _documents(args.root):
        total_docs += 1
        for rule in rules:
            found = list(rule.compiled().finditer(text))
            if not found:
                continue
            counts[rule.name] += len(found)
            docs[rule.name] += 1
            for match in found[: args.max]:
                if len(examples[rule.name]) >= args.max:
                    break
                start = max(0, match.start() - args.context)
                end = min(len(text), match.end() + args.context)
                snippet = text[start:end].replace("\n", " ").strip()
                examples[rule.name].append(f"{loc}: …{snippet}…")

    print(f"{total_docs} document(s) scanned\n")
    for rule in rules:
        n, d = counts[rule.name], docs[rule.name]
        print(f"{rule.name}  ->  {rule.replacement}")
        print(f"  {n} match(es) across {d} document(s)")
        if n and not args.counts_only:
            for line in examples[rule.name]:
                print(f"    {line[:160]}")
        if not n:
            # Worth saying out loud: a rule that never fires is not protection,
            # it is a rule someone will trust and it does nothing.
            print("    (never fires on this corpus)")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
