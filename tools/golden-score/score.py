#!/usr/bin/env python3
"""W-204 phase D — join a hand-off to the answer key and score it. Nothing else.

🔴 **ARPIT RUNS THIS, FROM HIS OWN SHELL, AND NO AGENT EVER INVOKES IT.** That
sentence is the whole of the permission under which this file exists:
[L11](../../records/0012_LAW-11-sealed-answer-key.md) **decision 13**, ratified
by Arpit on 2026-09-21. The sanctioned way to start it is `just golden-score`.

**Why it is shaped this way.** The guards that seal the key bind a Claude *tool
call*; a command Arpit types in his own terminal is not one. So this carve-out
needed **no hole in any guard** — all six stay byte-identical, and a session that
names a key path is refused today exactly as it was yesterday. If you are an
agent reading this: **you may read what this program writes, and you may not run
it.**

⚠ **This docstring previously claimed a lift that had not happened.** Until the
2026-09-21 amendment it read *"what remains of L11 after the lift"* and *"it runs
only after Arpit has opened the key"* — **there was no lift**, the file was
untracked, and no gate had seen it. A session that trusted it would have breached
in the one way L11 says does not fail loudly. The note stays because the next
confident-sounding file will read just like the last one.

**What it computes, mechanically, and nothing beyond:**

| | metric | from |
|---|---|---|
| `hit@k` | is any `relevant` document in the top k | the hand-off's `ranked`, the key's `relevant` |
| `primary_rank` | where the key's `primary` landed | the same |
| `abstain_correct` | the band said unanswerable AND the key agrees | `answerable` vs the key |
| `abstain_wrong` | the band said unanswerable AND the key says it is answerable | the same |
| `answered_unanswerable` | text returned for a question the key says has no answer | `answer_text` vs the key |
| `evidence_quoted` | the key's evidence quote appears in the answer text | a normalised substring test |

🔴 **`evidence_quoted` is a MECHANICAL PROXY and is NOT the answer-text verdict.**
W-204 phase D step 3 asks for `correct` · `partial` · `wrong` · `declined`
*"with the evidence quote as the criterion"*, and a substring test is not that
judgment: an answer can quote the right sentence and still be wrong about the
question, or paraphrase correctly and match nothing. **The proxy is reported
under its own name**, and the judged series
([SR-WORK-QUALITY](../../records/0056_WORK-quality.md)) pins model, prompt and
version when it is run. `answer_text_verdict` is emitted as `null` here, always.

🔴 **A row with no key line, or a key line with no row, is an ERROR and not a
skip** (phase D step 1). Silently dropping either is how a partial score comes to
look like a whole one.

🔴 **IT NEVER WRITES A KEY BYTE, AND IT EMITS NO ANSWER.** L11's first sentence
defines an *answer* as **answer text, an evidence quote, a `relevant` or
`primary` list, or an `answerable` flag**. None of those four reaches the output:
it carries question ids, ranks, booleans and counts, and nothing else. That
allow-list is decision 13's containment, and
[`tests/test_golden_score_output.py`](../../tests/test_golden_score_output.py)
pins it against a synthetic key so a later field cannot be added quietly.

⚠ **`answerable_key` used to be in every row** — the key's `answerable` flag,
copied verbatim, for every question. That is not a proxy for an answer; the law
names it as one. It was removed on 2026-09-21; `abstain_correct` and
`abstain_wrong` carry what the benchmark needs, and nothing had been scored with
it yet.

⚠ **Door 4, named in the law and NOT shut by this file.** A per-query row joined
against the hand-off it scored still infers part of a key: `primary_rank: 3` plus
that row's `ranked` list names the primary document. The allow-list keeps answers
out of the file; it cannot keep them out of the inference. Every number produced
here is `informed` permanently, and so is anything compared against it.

🔴 **The key is read from the one permitted directory and nowhere else.** A key
outside it is a breach under L11 decision 3 and this program refuses it, which is
why the keys left in a scratchpad on 2026-09-21 were refused rather than scored.

⚠ **It refuses a PARTIAL key by default.** A key missing ids the hand-off has is
the single most likely way to publish a score covering a fraction of the
benchmark while looking complete. `--allow-partial` exists, prints exactly what
is missing, and stamps `partial: true` on every output it writes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

KS = (1, 5, 10, 20, 50)


def read_jsonl(path: Path, *, redact: bool = False) -> dict[str, dict]:
    """Parse JSONL into `{id: row}`.

    ⚠ `redact=True` is used for the key, and it is not decoration. `json.loads`
    puts the offending text into `JSONDecodeError`, so an unhandled parse error
    on a key line would print key bytes to stderr — **a traceback is the output
    channel wearing a different hat**, and L11 decision 13's allow-list would be
    satisfied while the answer went out anyway. The line number is reported; the
    line is not.
    """
    out: dict[str, dict] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            if redact:
                raise SystemExit(
                    f"refusing: key line {n} is not valid JSON ({exc.msg}). "
                    "The line itself is withheld on purpose — L11 decision 13."
                ) from None
            raise
        out[row["id"]] = row
    return out


def _norm(text: str) -> str:
    """Whitespace-collapsed and case-folded. Nothing cleverer, on purpose: a
    normaliser that also stripped punctuation would make the proxy quietly
    generous, and a generous proxy is worse than no proxy."""
    return re.sub(r"\s+", " ", (text or "")).strip().casefold()


def score_one(row: dict, key: dict) -> dict:
    ranked = [r for r in (row.get("ranked") or []) if r]
    relevant = set(key.get("relevant") or [])
    primary = key.get("primary")
    answerable = bool(key.get("answerable"))
    text = row.get("answer_text") or ""

    hits = {f"hit@{k}": bool(relevant & set(ranked[:k])) for k in KS}
    primary_rank = ranked.index(primary) + 1 if primary and primary in ranked else None

    # The band is fux's abstention signal. Phase A measured `band: weak` and
    # `answerable: false` coinciding on 2 992 of 2 992 rows, so either field
    # reads the same; `answerable` is used because it is the explicit one.
    said_unanswerable = row.get("answerable") is False
    quotes = [_norm(e.get("quote", "")) for e in (key.get("evidence") or [])]
    body = _norm(text)

    return {
        "id": row["id"],
        # ⚠ `answerable_key` was here until 2026-09-21. It is the key's
        # `answerable` flag, verbatim — one of the four things L11's first
        # sentence CALLS an answer — published once per question. The counts
        # below carry what the benchmark needs. Do not put it back.
        "band": row.get("band"),
        "said_unanswerable": said_unanswerable,
        **hits,
        "primary_rank": primary_rank,
        "abstain_correct": said_unanswerable and not answerable,
        "abstain_wrong": said_unanswerable and answerable,
        "answered_unanswerable": (not answerable) and bool(body),
        # 🔴 a proxy, not a verdict — see the module docstring
        "evidence_quoted": any(q and q in body for q in quotes),
        "answer_text_verdict": None,  # the judged series fills this, never this file
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--handoff", type=Path, required=True)
    ap.add_argument("--key", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rung", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--set", dest="set_n", type=int, required=True)
    ap.add_argument("--allow-partial", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(__file__).resolve().parents[2]

    # 🔴 L11 decision 13 — the permission attaches to ARPIT'S HAND, not to this
    # file. The guards seal the key against a Claude *tool call*; a command typed
    # in a plain terminal is not one, which is the only reason this carve-out
    # needed no hole in any guard. So: if the environment says a Claude session
    # is what started us, stop. It is a tripwire, not a guarantee — an agent that
    # scrubs its own environment defeats it, and L11 is what binds that agent.
    # A false positive here is the true positive: `just golden-score` run from an
    # agent's integrated terminal is exactly the case the carve-out excludes.
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE_SESSION_ID"):
        print(
            "refusing: this looks like a Claude Code session's shell.\n"
            "  L11 decision 13 permits Arpit to run this from his OWN terminal and\n"
            "  permits no agent to invoke it, by any route. Open a plain shell.",
            file=sys.stderr,
        )
        return 2

    # 🔴 L11 decision 3 — one permitted address, and a key anywhere else is a
    # breach to DECLARE, never an input to score.
    sealed = (repo / "work" / "golden" / "golden-answers").resolve()
    key_path = args.key.resolve()
    if key_path != sealed and sealed not in key_path.parents:
        print(
            "refusing: the key must live in the one directory L11 decision 3 permits.\n"
            "  A key outside it is a breach to declare — file it, do not score it.",
            file=sys.stderr,
        )
        return 2

    resolved = args.out.resolve()
    inside = str(resolved).startswith(str(repo))
    if inside and "regression" not in resolved.parts:
        print("refusing: inside the repo, scores belong under work/regression/", file=sys.stderr)
        return 2

    rows, key = read_jsonl(args.handoff), read_jsonl(args.key, redact=True)
    missing_key = sorted(set(rows) - set(key))
    missing_row = sorted(set(key) - set(rows))
    if (missing_key or missing_row) and not args.allow_partial:
        print(
            "REFUSING — the join is incomplete, and a partial score looks like a whole one.\n"
            f"  {len(missing_key)} hand-off row(s) with no key line: {missing_key[:5]}\n"
            f"  {len(missing_row)} key line(s) with no hand-off row: {missing_row[:5]}\n"
            "  Pass --allow-partial to score anyway; every output is stamped partial.",
            file=sys.stderr,
        )
        return 1

    scored = [score_one(rows[i], key[i]) for i in sorted(rows.keys() & key.keys())]
    payload = {
        "rung": args.rung,
        "arm": args.arm,
        "set": args.set_n,
        "n": len(scored),
        "partial": bool(missing_key or missing_row),
        "missing_key_lines": missing_key,
        "missing_handoff_rows": missing_row,
        "totals": {
            **{f"hit@{k}": sum(1 for s in scored if s[f"hit@{k}"]) for k in KS},
            "primary_at_1": sum(1 for s in scored if s["primary_rank"] == 1),
            "abstain_correct": sum(1 for s in scored if s["abstain_correct"]),
            "abstain_wrong": sum(1 for s in scored if s["abstain_wrong"]),
            "answered_unanswerable": sum(1 for s in scored if s["answered_unanswerable"]),
            "evidence_quoted": sum(1 for s in scored if s["evidence_quoted"]),
        },
        "rows": scored,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    t = payload["totals"]
    flag = "  PARTIAL" if payload["partial"] else ""
    print(
        f"{args.arm}/{args.rung}/set-{args.set_n}: n={payload['n']} "
        f"hit@1={t['hit@1']} hit@5={t['hit@5']} primary@1={t['primary_at_1']} "
        f"abstain_ok={t['abstain_correct']} abstain_wrong={t['abstain_wrong']} "
        f"evidence_quoted={t['evidence_quoted']}{flag}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
