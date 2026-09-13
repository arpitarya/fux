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
FUX = ROOT / ".venv" / "bin" / "fux"
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

from verdict import FLOOR_OF_ALL_FLOORS, line as vline, rule as vrule  # noqa: E402

SEED = 20260912

#: Probe terms are COMPOSED, not listed, so the set can be widened without a
#: hand-written list drifting out of alphabetical or unique. Deterministic and
#: seedless: the same N terms for the same N, on any machine.
_A = ("zol", "quen", "mar", "vin", "kel", "ori", "thal", "pyr", "bex", "cin",
      "nyq", "sper", "dro", "ash", "mor", "tel", "hav", "bren", "ors", "wick",
      "gal", "olm", "syr", "dun", "fen", "lor", "tav", "esk", "rud", "pil")
_B = ("frane", "drix", "beth", "taro", "spar", "dune", "met", "rocol", "wald",
      "drol", "uath", "rin", "vane", "keld", "ivan", "quist", "orne", "disk",
      "alis", "mare")


def terms(n: int) -> list[str]:
    """`n` distinct nonsense tokens. 600 available before any repeat."""
    out = [a + b for b in _B for a in _A]
    assert len(set(out)) == len(out)
    return out[:n]


#: 90 probes, 30 per family. Wide enough that the exact test has room to
#: resolve: decision 19 needs a net of 12 at 30 discordant pairs.
TERMS = terms(90)

#: W-155's two families, on terms 90-149. **Kept as a separate slice so the
#: first 90 keep their terms and their family assignments** — `terms(n)` is a
#: prefix of `terms(n + k)`, so extending the list cannot renumber what exists.
#:
#: 🔴 **These invert the construction: the TABLE carries the query term.** Every
#: probe above uses a table of unrelated cells, so option (b) has only ever been
#: measured against a table that is an *appendix*. The compare doc names that
#: gap in its own recommendation, and these close it.
TABLE_TERMS = terms(150)[90:]

#: The families whose table carries the term, and which document is correct.
#:
#: - **`dump`** is the HARM case and the one the pre-registered question turns
#:   on: a data dump that names the term in a row and says nothing about it,
#:   against prose that discusses it. **The prose document is correct.** (b)
#:   collapses the dump's length; if it then wins, (b) over-promotes.
#: - **`content`** is the BENEFIT case: a rate card whose subject IS its rows.
#:   **The table-heavy document is correct**, and shipped `flen` punishes it for
#:   a length that is the answer rather than padding.
#:
#: `content` CANNOT answer the question — there the table-heavy document is the
#: better answer, so promoting it is correct by construction.
TABLE_FAMILIES = ("dump", "content")

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


def _table_with(rng: random.Random, tokens: int, term: str, hits: int) -> str:
    """A table whose CELLS carry the probe term `hits` times.

    🔴 **This is the whole of W-155's inversion.** `_table` above never emits a
    probe term, so every existing probe's table is an appendix: it lengthens the
    document and says nothing about the query. Here the term is *in the rows*,
    which is what a rate card is — and what option (b) has never been measured
    against.

    The term is placed in the FIRST column, the label position, because that is
    where a rate card carries its subject; scattering it through numeric cells
    would be a different document shape and a different claim.
    """
    header = "| item | carrier | window | status | note |"
    sep = "|---|---|---|---|---|"
    rows, used, n = [], 0, 0
    while used < tokens:
        label = term if n < hits else rng.choice(CELL_WORDS)
        cells = [label] + [rng.choice(CELL_WORDS) for _ in range(4)]
        rows.append("| " + " | ".join(cells) + " |")
        used += 5
        n += 1
    # The term lands in the first `hits` rows, which are the top of the table.
    # Position carries no weight in BM25F -- `body` tf is a count -- so this is
    # legibility for a reader of the corpus, not a thumb on the scale.
    return "\n".join([header, sep] + rows)


def _doc(title: str, prose: str, table: str | None) -> str:
    out = [f"---\ntitle: {title}\n---\n", f"# {title}\n", prose, ""]
    if table:
        out += ["## Schedule\n", table, ""]
    return "\n".join(out) + "\n"



def scaffold(dest: Path, types: list[str]) -> None:
    """Let `fux setup` write the repo, then declare the corpus.

    ⚠ **Hand-writing `fux.toml` was wrong and failed loudly, which is the point.**
    `[sources] dirs` stopped being a TOML key when SR-DIR-LIST landed, and a
    generator carrying its own copy of the config shape is a second source of
    truth that drifts silently. `fux setup` is the one that cannot.
    """
    # 🔴 `git init` FIRST, and it is not optional. The repo root is resolved by
    # walking up, and `~/my_programs/fux-lab/` carries its own `fux.toml` — so
    # without a root here `fux setup` silently adopts the LAB as the repo and
    # writes nothing in the corpus. It exits 0 while doing it.
    subprocess.run(["git", "init", "-q"], cwd=str(dest), check=True)
    r = subprocess.run([str(FUX), "setup", "--no-agents"], cwd=str(dest),
                       text=True, capture_output=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("fux setup failed")
    (dest / ".fux" / "sources" / "dirs").write_text(
        "# The generated corpus. Declared, never derived (SR-DIR-LIST).\ndocs\n",
        encoding="utf-8")
    # ⚠ **No types file is written, and the argument is kept only to document
    # that.** The list moved to `.fux/formats.toml` (SR-TYPES decision 12) and
    # `setup` writes the built-in default there — which already admits every
    # format these corpora use. A second list here is refused by name, which is
    # how this was found rather than guessed at.
    assert types, "the corpus must name the formats it depends on"


def cmd_gen(a) -> int:
    dest = Path(a.dest)
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "docs").mkdir(parents=True)
    scaffold(dest, ['.md'])

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

    # ---- W-155: the two families whose TABLE carries the query term ---------
    #
    # 🔴 Short prose on the table-heavy side is the point, not an economy. A rate
    # card is mostly rows; giving it 400 tokens of prose as well would make it a
    # prose document with an appendix, which is the family already measured.
    SHORT = max(1, P // 3)
    for k, term in enumerate(TABLE_TERMS):
        i = len(TERMS) + k
        fam = TABLE_FAMILIES[k % len(TABLE_FAMILIES)]
        heavy = f"docs/{i:03d}-{term}-export.md" if fam == "dump" else f"docs/{i:03d}-{term}-ratecard.md"
        prose_doc = f"docs/{i:03d}-{term}-analysis.md" if fam == "dump" else f"docs/{i:03d}-{term}-memo.md"
        if fam == "dump":
            # The dump NAMES the term in three rows and says nothing about it;
            # the analysis discusses it six times in ordinary prose.
            files[heavy] = _doc(f"{term.title()} export",
                                _prose(rng, term, 1, SHORT), _table_with(rng, TBL, term, 3))
            files[prose_doc] = _doc(f"{term.title()} analysis", _prose(rng, term, 6, P), None)
            subj, rival = prose_doc, heavy
            why = ("the table is a DATA DUMP: it names the term in 3 rows and says nothing "
                   "about it, against prose that discusses it 6 times. The prose document is "
                   "correct in BOTH arms, and (b) collapsing the dump's length must not change that")
        else:
            # The rate card IS its rows: the term is its subject, six times.
            files[heavy] = _doc(f"{term.title()} rate card",
                                _prose(rng, term, 1, SHORT), _table_with(rng, TBL, term, 6))
            files[prose_doc] = _doc(f"{term.title()} memo", _prose(rng, term, 3, P), None)
            subj, rival = heavy, prose_doc
            why = ("the table IS the answer: a rate card whose subject is its rows, 6 cells "
                   "against a memo's 3 prose mentions. Shipped `flen` punishes it for a length "
                   "that IS the content; (b) should fix that")
        probes.append({"id": f"{fam[0]}{i:03d}", "family": fam, "term": term,
                       "query": term, "relevant": subj, "rival": rival, "why": why})

    # Filler. Each mentions several probe terms ONCE, so every probe term's `df`
    # lands in the tens — the single change that unsaturates the endpoint the
    # 2026-09-12 run could not move.
    #
    # ⚠ **It samples ALL 150 terms since W-155**, so the three original families'
    # `df` differs from the 2026-09-12 corpus. That is why this corpus's `main`
    # numbers are a REPLICATION and not a continuation, and the pre-registration
    # says so before any of them existed.
    ALL_TERMS = TERMS + TABLE_TERMS
    for j in range(a.filler):
        picks = rng.sample(ALL_TERMS, 5)
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
    for fam in ("main", "inverse", "placebo", *TABLE_FAMILIES):
        print(f"  {fam:<8} {sum(1 for p in probes if p['family'] == fam)}")
    print(f"{len(files)} documents, {len(probes)} probes -> {dest}")
    return 0


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def _score(corpus: Path, probes: list[dict], quiet: bool = False):
    """Ingest, build, and rank every probe in both arms. Returns per-probe rows."""
    r = subprocess.run([str(PY), "-c",
                        "import sys;from fux.cli import main;"
                        "sys.argv=['fux','ingest','--full'];rc=main();"
                        "sys.argv=['fux','build'];raise SystemExit(rc or main())"],
                       cwd=str(corpus), text=True, encoding="utf-8", capture_output=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("ingest/build failed")

    import table_flen as T
    rows = T.measure(corpus)
    bad = [r_["loc"] for r_ in rows if not r_["agrees"]]
    if not quiet:
        print(f"verification gate: recomputed body length equals the committed value "
              f"on {len(rows) - len(bad)} / {len(rows)} documents")
    if bad:
        raise SystemExit(
            f"GATE FAILED on {len(bad)} documents - this tool is not measuring the "
            f"shipped pipeline. First few: {bad[:5]}")

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
    if not quiet:
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
    return out


def cmd_run(a) -> int:
    corpus = Path(a.corpus)
    probes = [json.loads(l) for l in (corpus / "probes.jsonl").read_text().splitlines()
              if l.strip()]
    out = _score(corpus, probes)

    print(f"\nprobe-term df: {min(r_['df'] for r_ in out)}-{max(r_['df'] for r_ in out)} "
          f"(the 2026-09-12 endpoint saturated at df == 1)")
    print()
    print(f"{'family':>9}  {'n':>3}  {'hit@1 shipped':>14}  {'hit@1 no-table':>15}  "
          f"{'discordant':>11}  {'net':>5}")
    res = {}
    for fam in ("main", "inverse", "placebo", *TABLE_FAMILIES):
        f_ = [r_ for r_ in out if r_["family"] == fam]
        s = sum(1 for r_ in f_ if r_["hit1_shipped"])
        c = sum(1 for r_ in f_ if r_["hit1_cf"])
        b = sum(1 for r_ in f_ if r_["hit1_cf"] and not r_["hit1_shipped"])
        w = sum(1 for r_ in f_ if r_["hit1_shipped"] and not r_["hit1_cf"])
        res[fam] = (len(f_), s, c, b, w)
        print(f"{fam:>9}  {len(f_):>3}  {s:>8} /{len(f_):<4}  {c:>9} /{len(f_):<4}  "
              f"{b + w:>11}  {b - w:>+5}")

    nq, s, c, b, w = res["main"]
    v = vrule(b, w, better="EXCLUDING table tokens from `flen` RANKS BETTER",
              worse="the SHIPPED `flen` RANKS BETTER")
    imp = sum(1 for r_ in out if r_["family"] == "main"
              and not (r_["hit1_shipped"] and r_["hit1_cf"]))
    reg = sum(1 for r_ in out if r_["family"] == "main"
              and (r_["hit1_shipped"] or r_["hit1_cf"]))
    print()
    print(f"[main] headroom improvement {imp}/{nq} · regression {reg}/{nq} "
          f"(SR-RS 22b; PROVEN under 22c(a) — the counterfactual arm is the "
          f"feature-off/on arm and the `inverse` family is its positive control)")
    print(f"[main] {vline(v)}")
    if v["outcome"] == "inconclusive":
        print("[main] INCONCLUSIVE (22d): not one probe moved between the arms.")
    elif v["outcome"] == "no detected change":
        print(f"[main] NO DETECTED CHANGE. The floor of all floors is "
              f"{FLOOR_OF_ALL_FLOORS}; at {v['discordant']} discordant pairs the bar "
              f"is a net of {v['net_needed']}. Do not lower it.")
    else:
        print(f"[main] {v['outcome']}.")

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

    # ---- W-155: the families whose TABLE carries the query term -------------
    for fam in TABLE_FAMILIES:
        if fam not in res:
            continue
        fnq, fs, fc, fb, fw = res[fam]
        f_ = [r_ for r_ in out if r_["family"] == fam]
        imp_f = sum(1 for r_ in f_ if not (r_["hit1_shipped"] or r_["hit1_cf"]))
        reg_f = sum(1 for r_ in f_ if r_["hit1_shipped"] and r_["hit1_cf"])
        print()
        print(f"[{fam}] headroom improvement {imp_f}/{fnq} · regression {reg_f}/{fnq} "
              f"(SR-RS 22b)")
        # 🔴 **Zero headroom in BOTH directions means two opposite things and the
        # difference is the whole of decision 22d.** With `discordant == 0` no
        # probe moved and there is nothing to measure. With `discordant == n`
        # EVERY probe moved and both headroom counts are zero because none is
        # right in both arms or wrong in both — the maximal-information case.
        # Printing the same warning for both would call a total flip a null.
        if imp_f == reg_f == 0:
            if fb + fw == fnq:
                print(f"[{fam}] every one of {fnq} probes is DISCORDANT — both headroom "
                      f"counts are zero because none is right in both arms or wrong in "
                      f"both. That is maximal information, NOT decision 22d's null.")
            else:
                print(f"[{fam}] 🔴 zero headroom in both directions with only {fb + fw} "
                      f"discordant — this family measures nothing; see SR-RS 22d.")
        if fam == "dump":
            # 🔴 The pre-registered question is read HERE and nowhere else.
            # `c` — the shipped arm right, the counterfactual wrong — is the
            # over-promotion the compare doc names as its unmeasured exposure.
            v_ = vrule(fb, fw,
                       better="excluding table tokens ALSO helps when the table is a data dump",
                       worse="🔴 (b) OVER-PROMOTES a data dump above the prose that answers")
            print(f"[dump] {vline(v_)}")
            if v_["outcome"] == "inconclusive":
                print("[dump] INCONCLUSIVE (22d): not one probe moved between the arms. "
                      "The pre-registered question is NOT answered.")
            elif v_["outcome"] == "no detected change":
                print(f"[dump] NO DETECTED CHANGE -> the pre-registered answer is NO and the "
                      f"gap CLOSES. Floor of all floors {FLOOR_OF_ALL_FLOORS}; at "
                      f"{v_['discordant']} discordant pairs the bar is a net of "
                      f"{v_['net_needed']}. Do not lower it.")
            else:
                print(f"[dump] {v_['outcome']}.")
        else:
            v_ = vrule(fb, fw,
                       better="excluding table tokens FIXES the rate-card case",
                       worse="excluding table tokens makes the rate-card case worse")
            print(f"[content] {vline(v_)}")
            print("[content] this family measures the UPSIDE and cannot answer the "
                  "pre-registered question: here the table-heavy document IS the better answer.")

    if a.json:
        dest = Path(a.json)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r_, sort_keys=True) + "\n" for r_ in out),
                        encoding="utf-8")
        print(f"\nper-probe rows ({len(out)}) -> {a.json}")
    return 0


def cmd_sweep(a) -> int:
    """Dose-response: at what table share does the shipped ranker start losing?

    🔴 **This exists because a single point is engineered and says so.** The
    `main` family's headline is measured at one table size, chosen by the author
    — so *"the counterfactual wins 30-0"* is partly a statement about that
    choice. A curve is not: it reports the share at which the defect begins to
    bite, which can be read against a real corpus's measured distribution
    (`rung-01000`: 31 % of documents at a table share >= 10 %, median 0.34).

    Everything but the table size is held fixed, and the corpus is regenerated
    from the same seed at each step, so the probes and the prose are identical
    across the sweep.
    """
    rows = []
    print(f"{'table tokens':>13}  {'share':>7}  {'hit@1 shipped':>14}  "
          f"{'hit@1 no-table':>15}  {'p':>9}  outcome")
    for tbl in a.sizes:
        ns = argparse.Namespace(dest=a.corpus, filler=a.filler, prose=a.prose, table=tbl)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_gen(ns)
        corpus = Path(a.corpus)
        probes = [json.loads(l) for l in (corpus / "probes.jsonl").read_text().splitlines()
                  if l.strip()]
        out = _score(corpus, probes, quiet=True)
        main = [r for r in out if r["family"] == "main"]
        s = sum(1 for r in main if r["hit1_shipped"])
        c = sum(1 for r in main if r["hit1_cf"])
        b = sum(1 for r in main if r["hit1_cf"] and not r["hit1_shipped"])
        w = sum(1 for r in main if r["hit1_shipped"] and not r["hit1_cf"])
        v = vrule(b, w, better="no-table better", worse="shipped better")
        share = tbl / (tbl + a.prose)
        print(f"{tbl:>13}  {share:>7.2f}  {s:>9} /{len(main):<3}  {c:>10} /{len(main):<3}  "
              f"{v['p']:>9.4f}  {v['outcome']}")
        rows.append({"table_tokens": tbl, "prose_tokens": a.prose,
                     "table_share_nominal": round(share, 4),
                     "n": len(main), "hit1_shipped": s, "hit1_no_table_flen": c, **v})
    print()
    print("The share at which the shipped arm starts losing is the number to read, "
          "not the 30-0 at one size. Compare it against the corpus you care about.")
    if a.json:
        dest = Path(a.json); dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                        encoding="utf-8")
        print(f"\nsweep rows ({len(rows)}) -> {a.json}")
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
    s = sub.add_parser("sweep"); s.add_argument("--corpus", required=True)
    s.add_argument("--sizes", type=int, nargs="+",
                   default=[0, 50, 100, 200, 400, 700, 1200, 2000])
    s.add_argument("--filler", type=int, default=150)
    s.add_argument("--prose", type=int, default=400)
    s.add_argument("--json"); s.set_defaults(fn=cmd_sweep)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
