#!/usr/bin/env python3
"""W-233 — where an identifier can STILL break after analyzer v3, measured.

**The research fixture the item orders before any design is compared.** Analyzer
v3 (W-205 family (a)) made `RF-118` survive whole; this asks the eight questions
[W-233](../../work/open/W-233-identifiers-retained-whole.md) lists about what it
did NOT cover, and answers each from the engine rather than from reading code:

- **Q1–Q6** run a fixed fixture of document/query pairs through the analyzer on
  **both readers** — Python in process, Node through `node/src/query/analyzer.mjs`
  — and classify every pair `WHOLE` (a whole-form term is shared), `PARTS` (only
  parts overlap) or `NONE`, plus Python/Node parity.
- **Q7** ingests a small scratch corpus with the real CLI and asks the real
  `fux ask --json`, so *"an exact ID loses to a shared-parts neighbour"* is a
  rank, not an inference.
- **Q8** analyzes a frozen rung's text (read-only) and counts what each candidate
  would add or shed in distinct terms and postings — no ingest, no arm.

It reads nothing under `work/golden/` — the fixture is authored here, the rung is
`fux-lab/corpora/golden/rung-*` (read, never written), and the Q7 corpus lives in
a temp directory that is deleted on exit.

    .venv/bin/python tools/quality-controls/identifier_fixture.py \\
        --rung rung-10000 --out work/regression/<run>/evidence
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.query.analyzer import analyze, split_identifier  # noqa: E402
from fux.query.stem import stem  # noqa: E402

LAB_RUNGS = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"

# (question, identifier as the document writes it, the query a person types)
CASES: list[tuple[str, str, str]] = [
    # Q1 · stemming the whole form
    ("Q1", "release-notes-2", "release-notes-2"),
    ("Q1", "PROJ-ALPHA-releases", "PROJ-ALPHA-releases"),
    ("Q1", "PROJ-ALPHA-releases", "PROJ-ALPHA-release"),
    ("Q1", "status-codes", "status-codes"),
    ("Q1", "DAIRY-2", "DAIRY-2"),
    ("Q1", "KFS-2014", "KFS-2014"),
    ("Q1", "QCL-OPS-DOCK-03", "QCL-OPS-DOCK-03"),
    ("Q1", "user_settings", "user_settings"),
    # Q2 · query/document mismatch
    ("Q2", "RF-118", "RF-118"),
    ("Q2", "RF-118", "rf-118"),
    ("Q2", "RF-118", "RF 118"),
    ("Q2", "RF-118", "rf118"),
    ("Q2", "RF-118", "RF–118"),  # en dash
    ("Q2", "RF-118", "RF—118"),  # em dash
    ("Q2", "RF-118", "RF‐118"),  # hyphen
    ("Q2", "RF-118", "RF−118"),  # minus sign
    ("Q2", "RF-118", "RF_118"),
    ("Q2", "RF–118", "RF-118"),  # the document is the one with the dash
    ("Q2", "RF118", "RF-118"),
    # Q3 · leading zeros
    ("Q3", "ADR-0004", "ADR-0004"),
    ("Q3", "ADR-0004", "ADR-4"),
    ("Q3", "ADR-4", "ADR-0004"),
    ("Q3", "ADR-0004", "ADR 4"),
    ("Q3", "QCL-OPS-DOCK-03", "QCL-OPS-DOCK-3"),
    # Q4 · separators v3 does not cover
    ("Q4", "JIRA:PROJ-1", "JIRA:PROJ-1"),
    ("Q4", "JIRA:PROJ-1", "PROJ-1"),
    ("Q4", "#1234", "#1234"),
    ("Q4", "ops@example", "ops@example"),
    ("Q4", "C++", "C++"),
    ("Q4", "v2.3.1+build.5", "v2.3.1+build.5"),
    ("Q4", "~/.fux", "~/.fux"),
    ("Q4", "run(fast)", "run(fast)"),
    ("Q4", "v2.3.1-rc.1", "v2.3.1-rc.1"),
    ("Q4", "v2.3.1-rc.1", "2.3.1-rc.1"),
    ("Q4", "v2.3.1", "2.3.1"),
    ("Q4", "v2.3.1", "v2.3.1"),
    # Q5 · long opaque IDs
    ("Q5", "d3139fdb8e4a2c1f0b9a7e6d5c4b3a2918f7e6d5", "d3139fdb8e4a2c1f0b9a7e6d5c4b3a2918f7e6d5"),
    ("Q5", "d3139fdb8e4a2c1f0b9a7e6d5c4b3a2918f7e6d5", "d3139fdb"),
    ("Q5", "d3139fdb8e4a2c1f0b9a7e6d5c4b3a2918f7e6d5", "d3139fd"),
    ("Q5", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440000"),
    ("Q5", "550e8400-e29b-41d4-a716-446655440000", "550E8400-E29B-41D4-A716-446655440000"),
    ("Q5", "550e8400-e29b-41d4-a716-446655440000", "550e8400"),
    # Q6 · paths and URLs
    ("Q6", "src/fux/query/bm25f.py", "src/fux/query/bm25f.py"),
    ("Q6", "src/fux/query/bm25f.py", "bm25f.py"),
    ("Q6", "src/fux/query/bm25f.py", "query/bm25f.py"),
    ("Q6", "src/fux/query/bm25f.py", "bm25f"),
    ("Q6", "https://example.com/wiki/RF-118?rev=2", "https://example.com/wiki/RF-118?rev=2"),
    ("Q6", "https://example.com/wiki/RF-118?rev=2", "RF-118"),
]

# The regex both readers apply, stated once for the per-case "whole" test: a term
# is a WHOLE form when it came from a raw token with a separator in it.
_SEP = re.compile(r"[-./_]")


def node_analyze(texts: list[str]) -> list[list[str]]:
    script = (
        'import {analyze} from "./node/src/query/analyzer.mjs";'
        'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>'
        "process.stdout.write(JSON.stringify(JSON.parse(s).map(analyze))));"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        input=json.dumps(texts), capture_output=True, text=True, encoding="utf-8",
        cwd=ROOT, check=True,
    )
    return json.loads(out.stdout)


def classify(doc: str, query: str, doc_terms: list[str], query_terms: list[str]) -> str:
    """`WHOLE` when a term spelling the identifier itself — the document's or the
    query's, lowercased — is on both sides; `PARTS` when only something else
    overlaps; `NONE` when nothing does. Spelling-based on purpose: "some shared
    term has a separator" misreads a 40-char sha (one token, no separator) as
    parts, and a URL's `rf` as whole."""
    shared = set(doc_terms) & set(query_terms)
    if not shared:
        return "NONE"
    return "WHOLE" if shared & {doc.lower(), query.lower()} else "PARTS"


def run_cases() -> list[dict]:
    texts = [t for _, d, q in CASES for t in (d, q)]
    node = node_analyze(texts)
    rows = []
    for i, (qn, doc, query) in enumerate(CASES):
        d_py, q_py = analyze(doc), analyze(query)
        d_js, q_js = node[2 * i], node[2 * i + 1]
        rows.append({
            "question": qn, "doc": doc, "query": query,
            "doc_terms": d_py, "query_terms": q_py,
            "outcome": classify(doc, query, d_py, q_py),
            "parity": d_py == d_js and q_py == q_js,
            # Q1's specific failure: a separator-bearing raw token whose exact
            # lowercased spelling never reached the index (the stemmer changed it).
            "whole_stemmed": any(split_identifier(w) and _SEP.search(w) and w.lower() not in d_py
                                 for w in _raw(doc)),
        })
    return rows


def _raw(text: str) -> list[str]:
    from fux.query.analyzer import _WORD_RE

    return _WORD_RE.findall(text)


# ---- Q7 · ranking ---------------------------------------------------------

FILLER = ("inventory ledger shift rota audit freezer supplier invoice delivery "
          "temperature checklist manager training cleaning allergen label batch "
          "recall storage dock pallet route store region report weekly quarterly").split()

Q7_DOCS: dict[str, str] = {
    "rf-118.md": "# Fryer recalibration\n\nRF-118 covers the fryer oil temperature "
                 "recalibration at the north kitchen. {fill}",
    "rf-119.md": "# Fryer rota\n\nRF-119 replaces RF-117 and RF-120. The RF team "
                 "logged 118 fryer checks and 118 oil changes; RF-119 is weekly. {fill}",
    "adr-0004.md": "# ADR-0004 storage format\n\nThe decision on the storage format. {fill}",
    "adr-0040.md": "# ADR-0040 labels\n\nADR-0040 supersedes ADR-0014; step 4 of 4 "
                   "and ADR 4 teams. {fill}",
    "v231.md": "# Release v2.3.1\n\nv2.3.1 fixes the dock pallet report. {fill}",
    "v230.md": "# Release v2.3.0\n\nv2.3.0 and v2.2.1 ship 3.1 times more routes; "
               "version 2.3 is current. {fill}",
    "sha.md": "# Rollback\n\nRolled back to d3139fdb8e4a2c1f0b9a7e6d5c4b3a2918f7e6d5 "
              "after the audit. {fill}",
    "bm25f.md": "# Scorer\n\nThe scorer lives in src/fux/query/bm25f.py. {fill}",
    "bm25.md": "# Old scorer\n\nsrc/fux/query/bm25.py and src/fux/query/rank.py "
               "hold the query code; fux query bm25 is the old path. {fill}",
}
Q7_QUERIES: list[tuple[str, str]] = [
    ("RF-118", "rf-118.md"), ("RF 118", "rf-118.md"), ("rf118", "rf-118.md"),
    ("RF–118", "rf-118.md"), ("what is RF-118", "rf-118.md"),
    ("ADR-0004", "adr-0004.md"), ("ADR-4", "adr-0004.md"), ("ADR 4", "adr-0004.md"),
    ("v2.3.1", "v231.md"), ("2.3.1", "v231.md"),
    ("d3139fdb", "sha.md"), ("d3139fdb8e4a2c1f0b9a7e6d5c4b3a2918f7e6d5", "sha.md"),
    ("bm25f.py", "bm25f.md"), ("src/fux/query/bm25f.py", "bm25f.md"),
]


def _fill(seed: int, n: int = 40) -> str:
    # Deterministic filler: a fixed walk over FILLER, no randomness (L4).
    return " ".join(FILLER[(seed * 7 + i * 3) % len(FILLER)] for i in range(n)) + "."


def run_ranking(fux: list[str]) -> list[dict]:
    tmp = Path(tempfile.mkdtemp(prefix="w233-q7-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
        docs = tmp / "docs"
        docs.mkdir()
        for i, (name, body) in enumerate(sorted(Q7_DOCS.items())):
            (docs / name).write_text(body.format(fill=_fill(i)) + "\n", encoding="utf-8")
        for i in range(20):  # neutral documents, so idf is not degenerate
            (docs / f"filler-{i:02d}.md").write_text(
                f"# Note {i}\n\n{_fill(100 + i, 80)}\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
        subprocess.run(["git", "-c", "user.name=w233", "-c", "user.email=w233@example.invalid",
                        "commit", "-qm", "fixture"], cwd=tmp, check=True)
        for verb in (["setup"], ["ingest"]):
            r = subprocess.run([*fux, *verb], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                raise SystemExit(f"fux {verb[0]} failed:\n{r.stderr}")
        rows = []
        for query, target in Q7_QUERIES:
            r = subprocess.run([*fux, "ask", "--json", "--top", "10", "--no-related", query],
                               cwd=tmp, capture_output=True, text=True, encoding="utf-8")
            hits = [Path(h["loc"]).name for h in _hits(r.stdout)]
            rank = hits.index(target) + 1 if target in hits else None
            rows.append({"query": query, "target": target, "rank": rank, "top3": hits[:3]})
        return rows
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _hits(stdout: str) -> list[dict]:
    data = json.loads(stdout) if stdout.strip() else {}
    if isinstance(data, list):
        return data
    for key in ("results", "hits", "documents"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


# ---- Q8 · cost on a rung --------------------------------------------------

_DIGIT = re.compile(r"\d")
_HEXISH = re.compile(r"^[0-9a-f]{7,40}$")


def shape(tok: str) -> str:
    """spaCy-style shape: letters X/x, digit runs d, punctuation kept, runs collapsed."""
    s = re.sub(r"[A-Z]+", "X", tok)
    s = re.sub(r"[a-z]+", "x", s)
    return re.sub(r"\d+", "d", s)


def run_cost(rung: Path) -> dict:
    tokens = 0
    terms: collections.Counter[str] = collections.Counter()   # df
    whole_terms: set[str] = set()
    whole_postings = whole_nodigit_postings = whole_stem_changed = 0
    whole_nodigit_terms: set[str] = set()
    stem_changed_terms: set[str] = set()
    families: dict[str, set[str]] = collections.defaultdict(set)
    family_docs: dict[str, set[str]] = collections.defaultdict(set)
    unicode_dash_docs = colon_docs = hash_docs = hex_docs = zero_pad_docs = 0
    dash_between_alnum_docs = 0
    files = sorted(p for d in ("seed", "ext") for p in (rung / d).rglob("*") if p.is_file())
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(rung))
        unicode_dash_docs += bool(re.search(r"[A-Za-z]+[‐-―−]\d", text))
        colon_docs += bool(re.search(r"\b[A-Z]{2,}:[A-Z]{2,}-\d", text))
        hash_docs += bool(re.search(r"(?<![\w&])#\d{2,}\b", text))
        hex_docs += bool(re.search(r"\b[0-9a-f]{7,40}\b(?=.*)", text) and
                         re.search(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b", text))
        # Any Unicode dash between two alphanumerics — the population a GLOBAL
        # dash fold would touch (numeric ranges `10–12`, not only IDs).
        dash_between_alnum_docs += bool(re.search(r"[A-Za-z0-9][\u2010-\u2015\u2212][A-Za-z0-9]", text))
        zero_pad_docs += bool(re.search(r"\b[A-Z]{2,}(?:-[A-Z]+)*-0\d+\b", text))
        doc_terms = analyze(text)
        tokens += len(doc_terms)
        uniq = set(doc_terms)
        terms.update(uniq)
        seen_whole: set[str] = set()
        for raw in _raw(text):
            if not split_identifier(raw) or not _SEP.search(raw):
                continue
            low = raw.lower()
            if low in seen_whole:
                continue
            seen_whole.add(low)
            whole_terms.add(low)
            whole_postings += 1
            if not _DIGIT.search(raw):
                whole_nodigit_postings += 1
                whole_nodigit_terms.add(low)
            if stem(low) != low:
                whole_stem_changed += 1
                stem_changed_terms.add(low)
            if _DIGIT.search(raw):
                prefix = re.match(r"[A-Za-z]*", raw).group(0)
                key = f"{prefix}|{shape(raw[len(prefix):])}"
                families[key].add(raw)
                family_docs[key].add(rel)
    qual = {k: (len(v), len(family_docs[k])) for k, v in families.items()
            if len(v) >= 3 and len(family_docs[k]) >= 2}
    top = sorted(qual.items(), key=lambda kv: (-kv[1][0], kv[0]))[:25]
    return {
        "rung": rung.name, "documents": len(files), "tokens": tokens,
        "distinct_terms": len(terms), "postings": sum(terms.values()),
        "whole_form": {"distinct": len(whole_terms), "postings": whole_postings},
        "whole_digit_free": {"distinct": len(whole_nodigit_terms), "postings": whole_nodigit_postings,
                             "examples": sorted(whole_nodigit_terms)[:15]},
        "whole_changed_by_stemming": {"distinct": len(stem_changed_terms),
                                      "postings": whole_stem_changed,
                                      "examples": sorted(stem_changed_terms)[:15]},
        "docs_with": {"unicode_dash_id": unicode_dash_docs, "colon_prefixed_id": colon_docs,
                      "hash_number": hash_docs, "hex_7_40": hex_docs,
                      "zero_padded_id": zero_pad_docs,
                      "unicode_dash_between_alnum": dash_between_alnum_docs},
        "families_qualifying_n3_m2": len(qual),
        # The lens design's question: how many survive once a family must carry
        # a literal letter prefix (dates, decimals and `400/hour` do not).
        "families_letter_prefixed": sum(1 for k in qual if k.split("|")[0]),
        "families_top": [{"family": k, "values": v[0], "docs": v[1],
                          "examples": sorted(families[k])[:4]} for k, v in top],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rung", default="rung-10000")
    ap.add_argument("--fux", default=str(ROOT / ".venv" / "bin" / "fux"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--skip-cost", action="store_true")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    rows = run_cases()
    with (args.out / "per-case-rows.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    by_q: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for r in rows:
        by_q[r["question"]][r["outcome"]] += 1
        by_q[r["question"]]["parity_fail"] += not r["parity"]
        by_q[r["question"]]["whole_stemmed"] += r["whole_stemmed"]
    print(f"{'q':<3} {'cases':>5} {'WHOLE':>5} {'PARTS':>5} {'NONE':>5} {'stemmed':>7} {'py!=js':>6}")
    for q in sorted(by_q):
        c = by_q[q]
        n = c["WHOLE"] + c["PARTS"] + c["NONE"]
        print(f"{q:<3} {n:>5} {c['WHOLE']:>5} {c['PARTS']:>5} {c['NONE']:>5} "
              f"{c['whole_stemmed']:>7} {c['parity_fail']:>6}")
    for r in rows:
        print(f"  {r['question']} {r['outcome']:<5} {r['doc']!r:<48} <- {r['query']!r}")

    ranking = run_ranking([args.fux])
    with (args.out / "ranking-rows.jsonl").open("w", encoding="utf-8") as fh:
        for r in ranking:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print("\nQ7 ranking (rank of the exact-ID document):")
    for r in ranking:
        print(f"  {r['query']!r:<46} {r['target']:<12} rank={r['rank']}  top3={r['top3']}")

    summary: dict = {"cases": {q: dict(c) for q, c in sorted(by_q.items())},
                     "ranking": ranking}
    if not args.skip_cost:
        cost = run_cost(LAB_RUNGS / args.rung)
        summary["cost"] = cost
        print("\nQ8 cost:", json.dumps(cost, indent=1, ensure_ascii=False))
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
