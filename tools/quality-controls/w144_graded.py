#!/usr/bin/env python3
"""W-144 — the graded set that answers *is the new order BETTER*.

## What the 2026-09-12 run established, and what it could not

[The run](../../work/regression/2026-09-12-priors-and-tables/report.md) §3 confirmed the
proposal's mechanism on the golden ladder and confirmed nothing about quality:

- **Headroom is large** — 31-35 % of documents carry a table share >= 10 %, the
  most table-heavy document's length normaliser would fall **58 %**, and
  `avg_wlen` at rung 1 000 moves 151.5 -> 133.8.
- **It moves ranking** — 16 of 124 top-1 results change at `rung-01000`.
- **In the predicted direction** — **41 of 44** top-1 changes across three rungs
  promote a *more* table-heavy document, 1 goes the other way.
- 🔴 **And the quality endpoint saturated.** A `df == 1` prose term scored 12/12
  in **both** arms at every dilution up to 16 terms. Its idf is simply
  unreachable by length normalisation. **Inconclusive (22d), not a null.**

> The endpoint with mechanical truth had no headroom; the endpoint with headroom
> had no truth.

## What this corpus changes, in one sentence

**Truth is PROSE DENSITY, and the rival document is a real competitor.**

Each probe is a pair sharing one nonsense term `T`:

| document | prose | occurrences of `T` in prose | table |
|---|---|---|---|
| **subject** (relevant) | ~400 tokens | **6** | ~900 tokens of unrelated cells |
| **rival** (not relevant) | ~400 tokens | **3** | none |

**Both documents say the same amount about everything else**, so the only
difference that bears on `T` is that the subject says twice as much about it in
the same amount of prose. That is the relevance judgement any annotator makes
and the one BM25 is built to encode — it is **not** the feature under test, so
the grading is not circular.

- **Shipped `flen`** counts the 900 table tokens, so the subject's length
  normaliser punishes it for words that have nothing to do with `T`, and the
  rival can win on a third of the evidence.
- **Table-excluded `flen`** makes the two lengths equal, so tf decides.

`T` appears once in each filler document as well, so its `df` is in the tens and
**idf cannot dominate the way a `df == 1` term's did**. That single change is
what unsaturates the endpoint.

## Two controls, and they are not decoration

- **`inverse`** — the same pair with the roles swapped: the **prose-only**
  document is the one with six occurrences and the table-heavy one has three.
  The correct answer is the prose-only document, in **both** arms. This is what
  catches a counterfactual that simply promotes table-heavy documents always,
  which would look identical to a win on the `main` family alone.
- **`placebo`** — two prose-only documents, 6 against 3, no table anywhere.
  Neither arm can differ. If it moves, something other than the feature is
  moving and the run is void.

⚠ **Both arms recompute `avg_wlen` from their own lengths, never borrow it** —
the M1 pruning gate's recorded error, and `table_flen.rank_arms` was written the
same way for the same reason.

⚠ **Scope.** This isolates the BM25F lexical ordering, as `rank_arms` does. It
does not apply `Weighting`, the declared tie-break or the reranker, because the
claim under test is about length normalisation and folding three other priors in
would measure their sum.

Usage:
    python3 tools/quality-controls/w144_graded.py gen --dest <dir>
    python3 tools/quality-controls/w144_graded.py run --corpus <dir> \
        --json work/regression/<run>/evidence/w144-graded.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "bin" / "python"
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

#: ADR-RS decision 19 — the floor of all floors. Never lowered to fit a result.
FLOOR = 6
SEED = 20260912

#: 24 probe terms. Nonsense, so `df` is the generator's choice and not English's.
TERMS = [
    "zolfrane", "quendrix", "marbeth", "vintaro", "kelspar", "oridune",
    "thalmet", "pyrrocol", "bexwald", "cindrol", "nyquath", "sperrin",
    "drovane", "ashkeld", "morrivan", "telquist", "havorne", "brendisk",
    "orsalis", "wickmare", "galdreth", "olmivar", "syrentha", "dunmarok",
]

PROSE_WORDS = (
    "consignment despatch tolerance interval calibration schedule handover "
    "register escalation supervisor ambient variance corridor threshold "
    "inspection clearance dispatch reconciliation allocation checkpoint"
).split()

CELL_WORDS = (
    "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima "
    "mike november oscar papa quebec romeo sierra tango"
).split()


def _prose(rng: random.Random, term: str, hits: int, tokens: int) -> str:
    """`tokens` words of ordinary prose with `term` in it exactly `hits` times."""
    words = [rng.choice(PROSE_WORDS) for _ in range(tokens - hits)]
    for pos in sorted(rng.sample(range(len(words)), hits)):
        words.insert(pos, term)
    lines, i = [], 0
    while i < len(words):
        lines.append(" ".join(words[i:i + 14]) + ".")
        i += 14
    return "\n".join(lines)


def _table(rng: random.Random, tokens: int) -> str:
    """A markdown table of unrelated cells. Its words are never a probe term."""
    header = "| lane | carrier | window | status | note |"
    sep = "|---|---|---|---|---|"
    rows, used = [], 0
    n = 0
    while used < tokens:
        cells = [rng.choice(CELL_WORDS) for _ in range(5)]
        rows.append("| " + " | ".join(cells) + " |")
        used += 5
        n += 1
    return "\n".join([header, sep] + rows)


def _doc(title: str, prose: str, table: str | None) -> str:
    out = [f"---\ntitle: {title}\n---\n", f"# {title}\n", prose, ""]
    if table:
        out += ["## Schedule\n", table, ""]
    return "\n".join(out) + "\n"


def cmd_gen(a) -> int:
    dest = Path(a.dest)
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "docs").mkdir(parents=True)
    (dest / ".fux").mkdir(parents=True, exist_ok=True)
    (dest / ".fux" / "pii.toml").write_text("", encoding="utf-8")

    rng = random.Random(SEED)
    files: dict[str, str] = {}
    probes: list[dict] = []
    P, TBL = a.prose, a.table

    for i, term in enumerate(TERMS):
        fam = ("main", "inverse", "placebo")[i % 3]
        if fam == "main":
            subj = f"docs/{i:03d}-{term}-schedule.md"
            rival = f"docs/{i:03d}-{term}-summary.md"
            files[subj] = _doc(f"{term.title()} schedule",
                               _prose(rng, term, 6, P), _table(rng, TBL))
            files[rival] = _doc(f"{term.title()} summary",
                                _prose(rng, term, 3, P), None)
            why = "subject says twice as much about the term in the same prose, and pays for a table"
        elif fam == "inverse":
            subj = f"docs/{i:03d}-{term}-summary.md"
            rival = f"docs/{i:03d}-{term}-schedule.md"
            files[subj] = _doc(f"{term.title()} summary",
                               _prose(rng, term, 6, P), None)
            files[rival] = _doc(f"{term.title()} schedule",
                                _prose(rng, term, 3, P), _table(rng, TBL))
            why = "roles swapped: the prose-only document is the relevant one in BOTH arms"
        else:
            subj = f"docs/{i:03d}-{term}-summary.md"
            rival = f"docs/{i:03d}-{term}-note.md"
            files[subj] = _doc(f"{term.title()} summary", _prose(rng, term, 6, P), None)
            files[rival] = _doc(f"{term.title()} note", _prose(rng, term, 3, P), None)
            why = "no table anywhere — neither arm can differ"
        probes.append({"id": f"{fam[0]}{i:02d}", "family": fam, "term": term,
                       "query": term, "relevant": subj, "rival": rival, "why": why})

    # Filler. Each mentions several probe terms ONCE, so every probe term's `df`
    # lands in the tens — the single change that unsaturates the endpoint the
    # 2026-09-12 run could not move.
    for j in range(a.filler):
        picks = rng.sample(TERMS, 5)
        body = "\n".join(
            f"Routine note {j:04d}. " + " ".join(rng.choice(PROSE_WORDS) for _ in range(20))
            + " " + t + "." for t in picks)
        files[f"docs/filler/{j:04d}-note.md"] = _doc(f"Operations note {j:04d}", body, None)

    for rel, body in sorted(files.items()):
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    (dest / "probes.jsonl").write_text(
        "".join(json.dumps(p, sort_keys=True) + "\n" for p in probes), encoding="utf-8")
    (dest / "fux.toml").write_text('[sources]\ndirs = ["docs"]\ntypes = [".md"]\n',
                                   encoding="utf-8")
    for fam in ("main", "inverse", "placebo"):
        print(f"  {fam:<8} {sum(1 for p in probes if p['family'] == fam)}")
    print(f"{len(files)} documents, {len(probes)} probes -> {dest}")
    return 0


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def cmd_run(a) -> int:
    corpus = Path(a.corpus)
    probes = [json.loads(l) for l in (corpus / "probes.jsonl").read_text().splitlines()
              if l.strip()]

    r = subprocess.run([str(PY), "-c",
                        "import sys;from fux.cli import main;"
                        "sys.argv=['fux','ingest','--full'];rc=main();"
                        "sys.argv=['fux','build'];raise SystemExit(rc or main())"],
                       cwd=str(corpus), text=True, capture_output=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("ingest/build failed")

    import table_flen as T
    rows = T.measure(corpus)
    bad = [r_["loc"] for r_ in rows if not r_["agrees"]]
    print(f"verification gate: recomputed body length equals the committed value on "
          f"{len(rows) - len(bad)} / {len(rows)} documents")
    if bad:
        print(f"🔴 GATE FAILED on {len(bad)} documents — this tool is not measuring the "
              f"shipped pipeline. First few: {bad[:5]}")
        return 1

    from fux.query.bm25f import DEFAULT_SCORING, derive_wlen, score_record
    from fux.query.scan import query_term_hashes
    from fux.store import TF_FIELDS, reader
    BODY = TF_FIELDS.index("body")

    records = [rec for rec in reader.read_index(corpus).values() if rec.get("loc")]
    cf_by_loc = {r_["loc"]: r_["table_tokens"] for r_ in rows}
    n = len(records)
    prepared, tot, tot_cf = [], 0.0, 0.0
    for rec in records:
        flen = list(rec.get("flen") or [])
        if not flen:
            continue
        flen += [0] * (len(TF_FIELDS) - len(flen))
        cf = list(flen)
        cf[BODY] = max(0, flen[BODY] - cf_by_loc.get(rec["loc"], 0))
        tot += derive_wlen(flen)
        tot_cf += derive_wlen(cf)
        prepared.append((rec, flen, cf))
    avg, cf_avg = tot / n, tot_cf / n
    print(f"corpus n={n}   avg_wlen {avg:.1f} -> {cf_avg:.1f} with table tokens out")

    out = []
    for p in probes:
        hashes = query_term_hashes(p["query"])
        df = {h: 0 for h in hashes}
        for rec, _f, _c in prepared:
            for h in hashes:
                if h in rec.get("terms", {}):
                    df[h] += 1
        a_, b_ = [], []
        for rec, flen, cf in prepared:
            terms = rec.get("terms", {})
            sa = score_record(terms, flen, hashes, df, n, avg, DEFAULT_SCORING)
            sb = score_record(terms, cf, hashes, df, n, cf_avg, DEFAULT_SCORING)
            if sa > 0:
                a_.append((sa, rec["loc"]))
            if sb > 0:
                b_.append((sb, rec["loc"]))
        rank_a = [loc for _s, loc in sorted(a_, key=lambda t: (-t[0], t[1]))][:10]
        rank_b = [loc for _s, loc in sorted(b_, key=lambda t: (-t[0], t[1]))][:10]
        out.append({**p, "df": max(df.values()),
                    "shipped": rank_a, "no_table_flen": rank_b,
                    "hit1_shipped": bool(rank_a) and rank_a[0] == p["relevant"],
                    "hit1_cf": bool(rank_b) and rank_b[0] == p["relevant"],
                    "rival1_shipped": bool(rank_a) and rank_a[0] == p["rival"],
                    "rival1_cf": bool(rank_b) and rank_b[0] == p["rival"]})

    print(f"\nprobe-term df: {min(r_['df'] for r_ in out)}-{max(r_['df'] for r_ in out)} "
          f"(the 2026-09-12 endpoint saturated at df == 1)")
    print()
    print(f"{'family':>9}  {'n':>3}  {'hit@1 shipped':>14}  {'hit@1 no-table':>15}  "
          f"{'discordant':>11}  {'net':>5}")
    res = {}
    for fam in ("main", "inverse", "placebo"):
        f_ = [r_ for r_ in out if r_["family"] == fam]
        s = sum(1 for r_ in f_ if r_["hit1_shipped"])
        c = sum(1 for r_ in f_ if r_["hit1_cf"])
        b = sum(1 for r_ in f_ if r_["hit1_cf"] and not r_["hit1_shipped"])
        w = sum(1 for r_ in f_ if r_["hit1_shipped"] and not r_["hit1_cf"])
        res[fam] = (len(f_), s, c, b, w)
        print(f"{fam:>9}  {len(f_):>3}  {s:>8} /{len(f_):<4}  {c:>9} /{len(f_):<4}  "
              f"{b + w:>11}  {b - w:>+5}")

    nq, s, c, b, w = res["main"]
    disc, net = b + w, abs(b - w)
    imp = sum(1 for r_ in out if r_["family"] == "main"
              and not (r_["hit1_shipped"] and r_["hit1_cf"]))
    reg = sum(1 for r_ in out if r_["family"] == "main"
              and (r_["hit1_shipped"] or r_["hit1_cf"]))
    print()
    print(f"[main] headroom improvement {imp}/{nq} · regression {reg}/{nq} "
          f"(ADR-RS 22b; PROVEN under 22c(a) — the counterfactual arm is the "
          f"feature-off/on arm and the `inverse` family is its positive control)")
    if disc == 0:
        print(f"[main] INCONCLUSIVE (22d): not one probe moved between the arms.")
    elif net >= FLOOR:
        which = "EXCLUDING table tokens from `flen`" if b > w else "the SHIPPED `flen`"
        print(f"[main] {which} RANKS BETTER: discordant {disc}, net {net} against a "
              f"floor of {FLOOR}.")
    else:
        print(f"[main] NO DETECTED CHANGE: discordant {disc}, net {net}, below the "
              f"floor of {FLOOR}. Do not lower the floor.")

    inq, is_, ic, ib, iw = res["inverse"]
    print()
    if is_ == ic == inq:
        print(f"[inverse] CONTROL HOLDS: both arms answer {inq}/{inq}. The "
              f"counterfactual is not simply promoting table-heavy documents.")
    else:
        print(f"[inverse] 🔴 CONTROL FAILED: shipped {is_}/{inq}, no-table {ic}/{inq}. "
              f"A counterfactual that loses prose-only relevance is not an improvement "
              f"whatever the `main` family says.")
    pnq, ps, pc, _pb, _pw = res["placebo"]
    if ps == pc:
        print(f"[placebo] CONTROL HOLDS: both arms score {ps}/{pnq}.")
    else:
        print(f"[placebo] 🔴 CONTROL BROKEN: shipped {ps}/{pnq} vs no-table {pc}/{pnq} "
              f"with no table in the family. The `main` number is not attributable.")

    if a.json:
        dest = Path(a.json)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r_, sort_keys=True) + "\n" for r_ in out),
                        encoding="utf-8")
        print(f"\nper-probe rows ({len(out)}) -> {a.json}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    g = sub.add_parser("gen"); g.add_argument("--dest", required=True)
    g.add_argument("--filler", type=int, default=150)
    g.add_argument("--prose", type=int, default=400)
    g.add_argument("--table", type=int, default=900)
    g.set_defaults(fn=cmd_gen)
    r = sub.add_parser("run"); r.add_argument("--corpus", required=True)
    r.add_argument("--json"); r.set_defaults(fn=cmd_run)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
