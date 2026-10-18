"""Corpus-mined expansion: `Long Form (ABBR)` pairs, folded at read time. W-168 step 4.

## What a document declares, and why fux may use it

A document that writes *"Mean Kinetic Temperature (MKT)"* has said, in its own
committed words, that the two spellings name one thing. A question asking about
*MKT* shares one rare token with that document and **none** with a document that
only ever writes the long form, and the reverse happens too. This module lets the
corpus supply the other spelling itself, through the `Expansion` object `--expand`
already ships ([SR-EXPAND](../../records/0149_expand.md)).

🔴 **No model is anywhere in it.** The pair is a regular-expression match on a
document's own text, analyzed by the one shared analyzer and hashed in the same
currency as `terms` ([L4](../../records/0006_LAW-4-deterministic.md)).

## Three halves, each in the one place it can live

| half | where | why there |
|---|---|---|
| **mine** | `mine()`, called by `ingest/extract.py` | a function of ONE document's bytes, so it is carried forward on an unchanged sha like `terms` |
| **commit** | the record's own `abbr` property, hashes only | 🔴 *a committed per-document byte is a function of that document alone* (W-168 §RULED 2026-09-15); hashes are statistics, not content ([L3](../../records/0005_LAW-3-content-never-durable.md)) |
| **fold** | `fold()`, over the union of every record's pairs | the table is corpus-wide, so it is rebuilt at read time — by `table_from_shards` on the scan, by the accelerator's derived `mined.json` on `--fast` — and **committed nowhere** |

## The shipped weight is `0.5`, MEASURED; `0.0` is the engine before this module

`0.5` is the first weight, ascending, that cleared the frozen bar; Arpit
ratified it on 2026-09-27 ([`VERDICT.md`](../../work/regression/2026-09-27-mined-expansion/VERDICT.md)).
`run_query` does not read a single pair when the weight is `0.0`, so no
arithmetic changes and no shard is re-read. The only trace of the feature on
the default path is that a line whose `abbr` carries a query hash is parsed by
the scan's prefilter — and `rank()` drops it at score `0`, so no output moves.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .. import store as store_mod
from .tokenize import tokenize

__all__ = ["PATTERN", "Pair", "fold", "mine", "pairs_from_line", "table_from_records", "table_from_shards"]

#: The weight is `.fux/tune.toml [ranking] mined_weight` — `0.5` as the
#: template ships it, W-168 step 4's measured value: the first to clear
#: [the frozen bar](../../work/regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md)
#: (6 wins, 0 losses, no baseline rank-1 hit lost), ratified PASS 2026-09-27.

#: The frozen pattern — [the pre-registration](../../work/regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md)
#: §The mechanism. It is the regex the `expansion_form` tag and the ruled pool
#: were counted with, **character for character**: a different pattern would
#: measure a different input than the one the bar was set on.
PATTERN = re.compile(r"\b((?:[A-Z][a-z]+[\s-]+){1,6}[A-Za-z]+)\s+\(([A-Z][A-Za-z]{1,6})\)")

#: One mined pair on the wire: `(short_hashes, long_hashes)`.
Pair = tuple[tuple[str, ...], tuple[str, ...]]

#: The committed property, off the raw bytes. **`abbr` sorts first** among the
#: record's keys (`canonical_dumps` sorts them), so it can only ever open the
#: line; anchoring on `{` means a title that happens to contain the word cannot
#: be mistaken for it. Every element is a quoted 16-hex hash, so the class
#: `[^\[\]]` never has to step over a nested bracket.
_ABBR_RE = re.compile(rb'^\{"abbr":(\[(?:\[\[[^\[\]]*\],\[[^\[\]]*\]\],?)+\])')


def _dedupe(tokens: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(tokens))


def mine(text: str) -> list[tuple[tuple[str, ...], tuple[str, ...]]]:
    """Every `Long Form (ABBR)` declaration in `text`, as ANALYZED tokens.

    Tokens, not hashes: ingest hashes them through the run's collision tracker,
    the same object `terms` and anchor terms go through, so a pair can never be
    written in a currency the postings do not use.

    - **short** = `analyze(ABBR)`; **long** = `analyze(Long Form)` with a
      leading `The ` dropped. (`the` is a stopword, so dropping it changes no
      hash; it is said here because the pre-registration says it.)
    - A pair whose either side analyzes to nothing is skipped — `(IT)` loses
      `it` to the stopword list and has no short side to fold.
    - A pair whose two sides are the same token set is skipped: it bridges
      nothing, and folding it would add no hash.

    Sorted and de-duplicated, so the committed bytes are a function of the set
    of declarations and not of the order a document happens to make them.
    """
    out: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
    for long_form, short_form in PATTERN.findall(text):
        if long_form.startswith("The "):
            long_form = long_form[len("The "):]
        short = _dedupe(tokenize(short_form))
        long = _dedupe(tokenize(long_form))
        if not short or not long or set(short) == set(long):
            continue
        out.add((short, long))
    return sorted(out)


def pairs_from_line(line: bytes) -> list[Pair]:
    """The committed `abbr` of one raw shard line, or `[]` without parsing it."""
    m = _ABBR_RE.match(line)
    if m is None:
        return []
    return [(tuple(s), tuple(l)) for s, l in json.loads(m.group(1))]


def table_from_records(records) -> tuple[Pair, ...]:
    """The corpus table from parsed records — the accelerator's build uses this."""
    table: set[Pair] = set()
    for record in records:
        for short, long in record.get("abbr", ()):
            table.add((tuple(short), tuple(long)))
    return tuple(sorted(table))


def table_from_shards(root: Path) -> tuple[Pair, ...]:
    """The corpus table from the committed shards — the scan's reference path.

    One byte-level pass that parses only the `abbr` prefix of a line that has
    one. Run only when `mined_weight > 0`, so the default path never pays it.
    """
    table: set[Pair] = set()
    for path in store_mod.iter_shard_paths(root):
        _, lines = store_mod.raw_record_lines(path)
        for line in lines:
            table.update(pairs_from_line(line))
    return tuple(sorted(table))


def fold(table, query_hashes: list[str]) -> list[str]:
    """The hashes the corpus adds to a query, in a deterministic order.

    For each pair `(A, B)`, **in sorted order**: if `A ⊆ Q` and `B ⊄ Q`, add
    `B \\ Q`; if `B ⊆ Q` and `A ⊄ Q`, add `A \\ Q`. Added hashes are
    de-duplicated first-seen, and within a side they keep the analyzer's order.

    Containment in both directions is the whole rule: a question that says
    *MKT* gains *mean kinetic temperature*, and one that spells it out gains
    *mkt*. A question carrying both sides already gains nothing.
    """
    q = set(query_hashes)
    added: dict[str, None] = {}
    for short, long in table:
        s_in = all(h in q for h in short)
        l_in = all(h in q for h in long)
        if s_in and not l_in:
            side = long
        elif l_in and not s_in:
            side = short
        else:
            continue
        for h in side:
            if h not in q:
                added.setdefault(h, None)
    return list(added)
