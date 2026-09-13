#!/usr/bin/env python3
"""W-144 — does a table inflate `flen`? The headroom check, before the measurement.

[`work/proposals/structure-aware-extraction.md`](../../work/proposals/structure-aware-extraction.md)
claims that table cells are tokenized into `body` like prose, so BM25F's length
normaliser reads a table-heavy document as **denser than it is** and ranks it
lower than it should for a term in its prose.

**This tool does not test the claim. It asks whether the claim can be tested on
this corpus** — the step the pruning gate and the `heading` control each skipped,
and paid a whole run for. SR-RS decision 22d: a null measured where nothing
could have moved is the absence of a measurement, not a negative result.

## What it computes, per document

Re-runs the **real** ingest path — `parse_document` then `extract._headings_and_body`
then `query.tokenize` — so the body token stream is exactly the one that produced
the committed `flen`, and is verified against it. Then it splits that body into

- **table tokens** — lines that are markdown table rows (`| … |`, separator rows
  included). Every decoded document arrives as Markdown (SR-DECODE decision 2),
  so an HTML `<table>` is a pipe table by the time extraction sees it and one
  rule covers every format.
- **prose tokens** — everything else.

and reports the counterfactual the proposal asks for: `wlen` with the table
tokens **removed from the body length**, against `wlen` as shipped.

`wlen = Σ FIELD_WEIGHTS[i] · flen[i]` is the only arithmetic that matters here,
and it comes from `query.bm25f.derive_wlen` rather than being re-implemented.

## What a result means

- **A document whose body is 0 % table has no headroom**, whatever the ranking
  does. The population that matters is the documents with a non-trivial table
  share, and this tool reports that population first — a corpus-wide mean would
  hide it exactly the way the M1 pruning gate's zero delta did.
- **`Δwlen/wlen` is the lever's size, not its effect.** It bounds how much
  length normalisation could move; whether that changes a ranked list is the
  measurement, and it is not this file.

Usage:
    python3 tools/quality-controls/table_flen.py --rung rung-01000
    python3 tools/quality-controls/table_flen.py --rung rung-01000 --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.ingest import pii as pii_mod  # noqa: E402
from fux.ingest.extract import _headings_and_body  # noqa: E402
from fux.ingest.parse import parse_document  # noqa: E402
from fux.query.bm25f import FIELD_WEIGHTS, derive_wlen  # noqa: E402
from fux.query.tokenize import tokenize  # noqa: E402
from fux.store import TF_FIELDS, reader  # noqa: E402

LAB = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"

#: A markdown table row. The separator row (`|---|---:|`) is a row too — it
#: carries no words, so it contributes no tokens, and including it costs
#: nothing while excluding it would need a second rule.
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")

BODY = TF_FIELDS.index("body")


def split_body(stripped_body: str) -> tuple[list[str], list[str]]:
    """(table tokens, prose tokens) from the exact text extraction tokenizes."""
    table_lines, prose_lines = [], []
    for line in stripped_body.splitlines():
        (table_lines if TABLE_ROW.match(line) else prose_lines).append(line)
    return tokenize("\n".join(table_lines)), tokenize("\n".join(prose_lines))


def measure(rung_dir: Path) -> list[dict]:
    records = reader.read_index(rung_dir)
    # Ingest redacts BEFORE it extracts (`ingest/run.py`), so a tool that skips
    # redaction tokenizes text the index never saw. It showed up immediately as
    # a 48-token gap on the `.eml`, whose addresses the default rules remove.
    pii_rules = pii_mod.load(rung_dir)
    by_loc = {r["loc"]: r for r in records.values() if r.get("loc")}
    rows = []
    for loc, rec in sorted(by_loc.items()):
        path = rung_dir / loc
        if not path.is_file():
            continue
        doc = parse_document(path.read_bytes(), loc, rung_dir)
        if doc is None:
            continue
        body, _hits = pii_mod.redact(pii_rules, doc.body)
        _headings, stripped = _headings_and_body(loc, body)
        table_toks, prose_toks = split_body(stripped)
        flen = list(rec.get("flen") or [])
        if not flen:
            continue
        flen = flen + [0] * (len(TF_FIELDS) - len(flen))

        # The check that makes the rest trustworthy: our body token count must
        # equal the one the index committed. If it does not, this tool is
        # measuring a different pipeline and every number below is fiction.
        recomputed = len(table_toks) + len(prose_toks)
        counterfactual = list(flen)
        counterfactual[BODY] = max(0, flen[BODY] - len(table_toks))
        wlen = derive_wlen(flen)
        cf_wlen = derive_wlen(counterfactual)
        rows.append({
            "loc": loc,
            "flen_body": flen[BODY],
            "recomputed_body": recomputed,
            "agrees": recomputed == flen[BODY],
            "table_tokens": len(table_toks),
            "prose_tokens": len(prose_toks),
            "table_share": (len(table_toks) / recomputed) if recomputed else 0.0,
            "wlen": round(wlen, 3),
            "wlen_no_tables": round(cf_wlen, 3),
            "delta_share": round((wlen - cf_wlen) / wlen, 4) if wlen else 0.0,
        })
    return rows


# --------------------------------------------------------------------------
# The ranking arm — does the lever move a ranked list?
# --------------------------------------------------------------------------
def rank_arms(rung_dir: Path, rows: list[dict], queries: list[dict], k: int = 10):
    """Rank every query twice: `flen` as shipped, and `flen` with table tokens
    removed from the body length.

    🔴 **Corpus statistics are RECOMPUTED in each arm, never borrowed.** The
    counterfactual changes `avg_wlen` as well as each document's `wlen`, and
    borrowing the shipped average would make the scores line up while measuring
    a system nobody could ship — the exact error CLAUDE.md records from the M1
    pruning gate.

    ⚠ **Scope, stated rather than implied.** This isolates the BM25F **lexical
    ordering**. It does not apply `Weighting` (archived, superseded, recency),
    the declared tie-break, or the reranker, so it is not the shipped pipeline's
    final order. That is deliberate: the proposal's claim is about length
    normalisation, and folding three other priors in would measure their sum.
    """
    from fux.query.bm25f import DEFAULT_SCORING, score_record
    from fux.query.scan import query_term_hashes

    records = [r for r in reader.read_index(rung_dir).values() if r.get("loc")]
    cf_by_loc = {r["loc"]: r["table_tokens"] for r in rows}

    def flens(record):
        flen = list(record.get("flen") or [])
        if not flen:
            return None, None
        flen = flen + [0] * (len(TF_FIELDS) - len(flen))
        cf = list(flen)
        cf[BODY] = max(0, flen[BODY] - cf_by_loc.get(record["loc"], 0))
        return flen, cf

    n = len(records)
    total_wlen = total_cf = 0.0
    prepared = []
    for record in records:
        flen, cf = flens(record)
        if flen is None:
            continue
        total_wlen += derive_wlen(flen)
        total_cf += derive_wlen(cf)
        prepared.append((record, flen, cf))
    avg, cf_avg = total_wlen / n, total_cf / n

    out = []
    for q in queries:
        hashes = query_term_hashes(q["question"])
        df = {h: 0 for h in hashes}
        for record, _f, _c in prepared:
            terms = record.get("terms", {})
            for h in hashes:
                if h in terms:
                    df[h] += 1
        a, b = [], []
        for record, flen, cf in prepared:
            terms = record.get("terms", {})
            sa = score_record(terms, flen, hashes, df, n, avg, DEFAULT_SCORING)
            sb = score_record(terms, cf, hashes, df, n, cf_avg, DEFAULT_SCORING)
            if sa > 0:
                a.append((sa, record["loc"]))
            if sb > 0:
                b.append((sb, record["loc"]))
        a = [loc for _s, loc in sorted(a, key=lambda t: (-t[0], t[1]))][:k]
        b = [loc for _s, loc in sorted(b, key=lambda t: (-t[0], t[1]))][:k]
        share = {r["loc"]: r["table_share"] for r in rows}
        out.append({"id": q["id"], "shipped": a, "no_table_flen": b,
                    "top1_changed": bool(a and b and a[0] != b[0]),
                    "topk_changed": a != b,
                    # The DIRECTION the proposal predicts: with table tokens out
                    # of the length, a table-heavy document should RISE. This is
                    # mechanical and needs no answer key — it says the mechanism
                    # is the claimed one, never that the new order is better.
                    "shipped_top1_share": round(share.get(a[0], 0.0), 4) if a else None,
                    "cf_top1_share": round(share.get(b[0], 0.0), 4) if b else None})
    return out, {"n": n, "avg_wlen": round(avg, 3), "cf_avg_wlen": round(cf_avg, 3)}




# --------------------------------------------------------------------------
# The key-free quality endpoint — the proposal's claim, stated as a probe
# --------------------------------------------------------------------------
def prose_probes(rung_dir: Path, rows: list[dict], threshold: float,
                 max_terms: int = 3, dilute: int = 0):
    """Build a probe per table-heavy document from terms in ITS PROSE ONLY.

    The proposal's claim in one sentence: *a table-heavy document ranks lower
    than it should **for a term that appears in its prose**.* That sentence is a
    probe, and its ground truth is **mechanical** — no answer key, no judgement:

    - take a document whose body is at least `threshold` table tokens;
    - find terms that occur in its **prose** and **not** in its own table rows,
      and whose corpus `df` is exactly **1** — so the document is the only place
      that term exists, and it is the correct answer by construction;
    - query for those terms and see where the document lands, in both arms.

    ⚠ **`df == 1` is what makes this honest.** A probe built from a term two
    documents share has no single correct answer, and grading it would need the
    judgement this endpoint exists to avoid. Terms are taken in sorted order so
    the probe set is byte-identical on every run.
    """
    from fux.query.bm25f import DEFAULT_SCORING, score_record
    from fux.query.scan import query_term_hashes

    records = [r for r in reader.read_index(rung_dir).values() if r.get("loc")]
    by_loc = {r["loc"]: r for r in records}
    pii_rules = pii_mod.load(rung_dir)

    # corpus df over every hash present, once
    df_all: dict[str, int] = {}
    for r in records:
        for h in (r.get("terms") or {}):
            df_all[h] = df_all.get(h, 0) + 1

    probes = []
    for row in sorted(rows, key=lambda r: r["loc"]):
        if row["table_share"] < threshold:
            continue
        loc = row["loc"]
        doc = parse_document((rung_dir / loc).read_bytes(), loc, rung_dir)
        if doc is None:
            continue
        body, _ = pii_mod.redact(pii_rules, doc.body)
        _h, stripped = _headings_and_body(loc, body)
        table_toks, prose_toks = split_body(stripped)
        table_set = set(table_toks)
        # candidate words: in prose, not in this document's own table rows
        seen, picked = set(), []
        for word in prose_toks:
            if word in table_set or word in seen:
                continue
            seen.add(word)
            hs = query_term_hashes(word)
            if len(hs) == 1 and df_all.get(hs[0], 0) == 1 and hs[0] in (by_loc[loc].get("terms") or {}):
                picked.append(word)
        if not picked:
            continue
        terms = sorted(picked)[:max_terms]
        # ⚠ DILUTION, and why it is not cheating. A `df == 1` term alone
        # saturates: it identifies its document whatever the length normaliser
        # does, so the probe returns 12/12 in BOTH arms and measures nothing —
        # the 2026-08-28 `heading` control's failure exactly. Mixing in the
        # document's most COMMON prose terms creates competition without
        # touching the truth: the answer is still the only document that
        # contains every query term, because one of them has `df == 1`.
        if dilute:
            common = sorted(
                ((df_all.get(query_term_hashes(w)[0], 0), w)
                 for w in seen if query_term_hashes(w) and w not in table_set),
                reverse=True)
            terms += [w for _d, w in common[:dilute]]
        probes.append({"loc": loc, "table_share": round(row["table_share"], 4),
                       "dilute": dilute, "query": " ".join(terms)})
    return probes, records, df_all


def run_prose_probes(rung_dir: Path, rows: list[dict], threshold: float, dilute: int = 0):
    from fux.query.bm25f import DEFAULT_SCORING, score_record
    from fux.query.scan import query_term_hashes

    probes, records, _df_all = prose_probes(rung_dir, rows, threshold, dilute=dilute)
    cf_by_loc = {r["loc"]: r["table_tokens"] for r in rows}

    n = len(records)
    prepared, total_wlen, total_cf = [], 0.0, 0.0
    for record in records:
        flen = list(record.get("flen") or [])
        if not flen:
            continue
        flen = flen + [0] * (len(TF_FIELDS) - len(flen))
        cf = list(flen)
        cf[BODY] = max(0, flen[BODY] - cf_by_loc.get(record["loc"], 0))
        total_wlen += derive_wlen(flen)
        total_cf += derive_wlen(cf)
        prepared.append((record, flen, cf))
    avg, cf_avg = total_wlen / n, total_cf / n

    out = []
    for probe in probes:
        hashes = query_term_hashes(probe["query"])
        df = {h: sum(1 for r, _f, _c in prepared if h in (r.get("terms") or {})) for h in hashes}
        a, b = [], []
        for record, flen, cf in prepared:
            terms = record.get("terms", {})
            sa = score_record(terms, flen, hashes, df, n, avg, DEFAULT_SCORING)
            sb = score_record(terms, cf, hashes, df, n, cf_avg, DEFAULT_SCORING)
            if sa > 0:
                a.append((sa, record["loc"]))
            if sb > 0:
                b.append((sb, record["loc"]))
        a = [loc for _s, loc in sorted(a, key=lambda t: (-t[0], t[1]))]
        b = [loc for _s, loc in sorted(b, key=lambda t: (-t[0], t[1]))]
        rank_a = a.index(probe["loc"]) + 1 if probe["loc"] in a else None
        rank_b = b.index(probe["loc"]) + 1 if probe["loc"] in b else None
        out.append({**probe, "rank_shipped": rank_a, "rank_no_table_flen": rank_b,
                    "hit1_shipped": rank_a == 1, "hit1_cf": rank_b == 1})
    return out



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", required=True)
    ap.add_argument("--json")
    ap.add_argument("--threshold", type=float, default=0.10,
                    help="table share above which a document counts as table-bearing")
    ap.add_argument("--rank", action="store_true",
                    help="also rank every released question in both arms")
    ap.add_argument("--rank-json")
    ap.add_argument("--prose-probe", action="store_true",
                    help="the key-free quality endpoint: a df==1 prose term per table-heavy document")
    ap.add_argument("--probe-json")
    ap.add_argument("--dilute", type=int, default=0,
                    help="mix in this many of the document's commonest prose terms, to give the probe competition")
    a = ap.parse_args()

    rung_dir = LAB / a.rung
    rows = measure(rung_dir)
    disagree = [r for r in rows if not r["agrees"]]
    bearing = [r for r in rows if r["table_share"] >= a.threshold]
    any_table = [r for r in rows if r["table_tokens"] > 0]

    print(f"rung: {a.rung}   documents measured: {len(rows)}")
    print(f"field weights: {dict(zip(TF_FIELDS, FIELD_WEIGHTS))}")
    if disagree:
        print(f"🔴 {len(disagree)} document(s) do NOT reproduce the committed flen[body]; "
              f"this tool is measuring a different pipeline. First few:")
        for r in disagree[:5]:
            print(f"    {r['loc']}  committed {r['flen_body']}  recomputed {r['recomputed_body']}")
        return 1
    print(f"✅ all {len(rows)} documents reproduce the committed flen[body] exactly")
    print()
    print(f"documents with ANY table token:            {len(any_table):5} "
          f"({100*len(any_table)/max(1,len(rows)):.1f} %)")
    print(f"documents with table share >= {a.threshold:.0%}:        {len(bearing):5} "
          f"({100*len(bearing)/max(1,len(rows)):.1f} %)   <- the population with headroom")
    if bearing:
        shares = sorted(r["table_share"] for r in bearing)
        deltas = sorted(r["delta_share"] for r in bearing)
        print(f"  table share   median {shares[len(shares)//2]:.3f}   max {shares[-1]:.3f}")
        print(f"  wlen delta    median {deltas[len(deltas)//2]:.3f}   max {deltas[-1]:.3f}")
        print()
        print("  the ten most table-heavy documents:")
        for r in sorted(bearing, key=lambda r: -r["table_share"])[:10]:
            print(f"    {r['table_share']:.3f} share  Δwlen {r['delta_share']:.3f}  "
                  f"body {r['flen_body']:5}  {r['loc']}")
    else:
        print("  🔴 ZERO headroom: no document carries a table share above the threshold.")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print(f"\nper-document rows -> {a.json}")

    if a.rank:
        qs = [json.loads(l) for l in
              (ROOT / "work/golden/questions/questions.jsonl").read_text().splitlines() if l.strip()]
        per_query, stats = rank_arms(rung_dir, rows, qs)
        moved1 = [r["id"] for r in per_query if r["top1_changed"]]
        movedk = [r["id"] for r in per_query if r["topk_changed"]]
        print()
        print(f"ranking arms  n={stats['n']}  avg_wlen {stats['avg_wlen']} -> "
              f"{stats['cf_avg_wlen']} without table tokens")
        print(f"  queries whose TOP-1 changes:   {len(moved1):3} / {len(per_query)}")
        print(f"  queries whose TOP-10 changes:  {len(movedk):3} / {len(per_query)}")
        if moved1:
            print("  top-1 movers: " + " ".join(moved1[:30]))
            up = sum(1 for r in per_query if r["top1_changed"]
                     and (r["cf_top1_share"] or 0) > (r["shipped_top1_share"] or 0))
            down = sum(1 for r in per_query if r["top1_changed"]
                       and (r["cf_top1_share"] or 0) < (r["shipped_top1_share"] or 0))
            print(f"  direction: the new top-1 is MORE table-heavy in {up} of "
                  f"{len(moved1)}, less in {down}  <- the proposal predicts MORE")
        if a.rank_json:
            Path(a.rank_json).write_text(
                "".join(json.dumps(r) + chr(10) for r in per_query), encoding="utf-8")
            print(f"  per-query rows -> {a.rank_json}")

    if a.prose_probe:
        probes = run_prose_probes(rung_dir, rows, a.threshold, dilute=a.dilute)
        h1a = sum(1 for p in probes if p["hit1_shipped"])
        h1b = sum(1 for p in probes if p["hit1_cf"])
        fixed = [p for p in probes if p["hit1_cf"] and not p["hit1_shipped"]]
        broken = [p for p in probes if p["hit1_shipped"] and not p["hit1_cf"]]
        print()
        print(f"prose probes (df==1 term from a table-heavy document's prose): {len(probes)}")
        print(f"  hit@1 shipped            {h1a} / {len(probes)}")
        print(f"  hit@1 no-table-flen      {h1b} / {len(probes)}")
        print(f"  fixed {len(fixed)}   broken {len(broken)}   discordant {len(fixed)+len(broken)}")
        for p in probes:
            if p["rank_shipped"] != p["rank_no_table_flen"]:
                print(f"    rank {p['rank_shipped']} -> {p['rank_no_table_flen']}  "
                      f"share {p['table_share']:.3f}  {p['loc']}")
        if a.probe_json:
            Path(a.probe_json).write_text(
                "".join(json.dumps(p) + chr(10) for p in probes), encoding="utf-8")
            print(f"  per-probe rows -> {a.probe_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
