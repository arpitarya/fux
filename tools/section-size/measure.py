"""W-236 Part A step 2 — what SR-SECTIONS would add to the committed index.

Read-only. For each rung it reads the rung's committed index (for the document
list and the doc plane's exact bytes), each document's source file, the rung's
own PII rules and identifier families, and the chunker's heading grammar. It
builds the section records SR-SECTIONS decisions 2-5 describe **in memory**,
encodes them with the engine's canonical encoder, and counts bytes. It writes
nothing but the JSON named by `--out`.

    .venv/bin/python tools/section-size/measure.py \
        --ladder ~/my_programs/fux-lab/corpora/golden \
        --out work/regression/2026-09-30-section-size/evidence/sizes.json

⚠ The index-section rule below is SR-SECTIONS decision 2, written here because
it is not built. It reuses `refer/_chunk.py`'s `_sections` and `_title_index`
unchanged; the one difference from the chunker's `_fold` is the fold test:
**bodiless**, not **shorter than `[refer] min_passage_bytes`**, so no tunable
reaches a committed byte.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux import store  # noqa: E402
from fux.decode._markdown import headings as md_headings  # noqa: E402
from fux.decode._markdown import strip_headings  # noqa: E402
from fux.ingest import pii as pii_mod  # noqa: E402
from fux.ingest.extract import _headings_and_body  # noqa: E402
from fux.ingest.parse import parse_document  # noqa: E402
from fux.query import identifiers as ids_mod  # noqa: E402
from fux.query.tokenize import tokenize  # noqa: E402
from fux.refer._chunk import _sections  # noqa: E402

def _fill_missing_limits() -> None:
    """The rungs' `.fux/formats.toml` predates W-225's `[limits]` keys, and the
    engine refuses a missing key (L12). `fux doctor --fix` would write them
    from the template; this tool may write nothing into fux-lab, so the same
    template values are merged IN MEMORY, for a key the rung lacks only."""
    from fux.decode import _limits

    original = _limits._load

    def filled(root: Path) -> dict:
        have = original(root) or {}
        merged = {d: dict(v) for d, v in _limits.template_limits().items()}
        for decoder, keys in have.items():
            merged.setdefault(decoder, {}).update(keys)
        return merged

    _limits._load = filled


_fill_missing_limits()

RUNGS = ("rung-seed", "rung-00100", "rung-00200", "rung-00500",
         "rung-01000", "rung-02000", "rung-05000", "rung-10000")


def index_sections(body: str) -> list[str]:
    """SR-SECTIONS decision 2: the section texts, in document order.

    `_sections` cuts at every heading (preamble included, whitespace-only
    sections dropped). A section whose text is ONLY its heading line folds
    forward into the next section when that one is strictly deeper — the
    title (`_title_index`) is always such a section. Nothing here reads a
    byte count.
    """
    secs = _sections(body)
    # `_title_index` names a section that is bodiless AND followed by a deeper
    # one, so the rule below already folds it; nothing else is special-cased.
    out: list[str] = []
    carry: list[str] = []
    for i, (heading, level, text, _s, _e) in enumerate(secs):
        nxt = secs[i + 1] if i + 1 < len(secs) else None
        bodiless = bool(heading) and "\n" not in text.strip()
        nested = nxt is not None and nxt[1] > level
        if bodiless and nested:
            carry.append(text)
            continue
        out.append("\n\n".join(carry + [text]))
        carry = []
    if carry:
        out.append("\n\n".join(carry))
    return out


def section_record(parent: str, k: int, text: str, ids) -> tuple[dict, int, int]:
    hs = md_headings(text)
    heading_tokens = tokenize(" ".join(h.text for h in hs), ids)
    body_tokens = tokenize(strip_headings(text), ids)
    b, h = Counter(body_tokens), Counter(heading_tokens)
    terms = {store.term_hash(t): store.trim((b[t], h[t])) for t in set(b) | set(h)}
    rec = {"id": f"{parent}#s{k}", "flen": store.trim((len(body_tokens), len(heading_tokens))), "terms": terms}
    return rec, len(body_tokens), len(heading_tokens)


def pct(xs: list[int], q: float) -> int:
    if not xs:
        return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def measure(rung: Path) -> dict:
    # The rungs predate W-233 and carry no `.fux/identifiers.toml`: no
    # families, which is what their index was written with.
    ids = ids_mod.for_root(rung) if ids_mod.path(rung).exists() else ids_mod.EMPTY
    rules = pii_mod.load(rung)
    doc_bytes = 0
    doc_zlib = 0
    doc_max_file = 0
    for p in store.iter_shard_paths(rung):
        raw = p.read_bytes()
        doc_bytes += len(raw)
        doc_zlib += len(zlib.compress(raw, 6))
        doc_max_file = max(doc_max_file, len(raw))
    records = store.read_index(rung)
    sec_shards: dict[str, list[bytes]] = {}
    per_doc: list[int] = []
    by_ext: Counter = Counter()
    nsec_bytes = 0
    empty_sections = 0
    totality_miss: list[str] = []
    unreadable = 0
    for doc_id, rec in sorted(records.items()):
        if rec.get("src") != "git":
            continue
        path = rung / rec["loc"]
        doc = parse_document(path.read_bytes(), rec["loc"], rung)
        if doc is None:
            unreadable += 1
            continue
        body = pii_mod.redact(rules, doc.body)[0] if rules else doc.body
        texts = index_sections(body)
        if len(texts) <= 1:
            continue
        per_doc.append(len(texts))
        by_ext[Path(rec["loc"]).suffix.lower()] += len(texts)
        nsec_bytes += len(f',"nsec":{len(texts)}'.encode())
        shard = store.shard_for(doc_id)
        sb = sh = 0
        for k, text in enumerate(texts, start=1):
            srec, nb, nh = section_record(doc_id, k, text, ids)
            sb += nb
            sh += nh
            if not srec["flen"]:
                empty_sections += 1
            sec_shards.setdefault(shard, []).append(store.canonical_dumps(srec))
        hs, stripped = _headings_and_body(rec["loc"], body)
        if (sb, sh) != (len(tokenize(stripped, ids)), len(tokenize(" ".join(hs), ids))):
            totality_miss.append(doc_id)
    header = store.canonical_dumps(store.HEADER)
    sec_bytes = sec_zlib = sec_max_file = 0
    for lines in sec_shards.values():
        data = header + b"".join(sorted(lines))
        sec_bytes += len(data)
        sec_zlib += len(zlib.compress(data, 6))
        sec_max_file = max(sec_max_file, len(data))
    added = sec_bytes + nsec_bytes
    return {
        "documents": len(records),
        "unreadable": unreadable,
        "multi_section_documents": len(per_doc),
        "section_records": sum(per_doc),
        "sections_per_multi_doc": {
            "mean": round(statistics.mean(per_doc), 2) if per_doc else 0,
            "p50": pct(per_doc, 0.5), "p90": pct(per_doc, 0.9), "max": max(per_doc, default=0),
        },
        "section_records_by_extension": dict(by_ext.most_common()),
        "empty_section_records": empty_sections,
        "doc_plane_bytes": doc_bytes,
        "section_plane_bytes": sec_bytes,
        "nsec_bytes": nsec_bytes,
        "added_bytes": added,
        "growth_pct": round(100 * added / doc_bytes, 1),
        "projected_total_bytes": doc_bytes + added,
        "largest_file_bytes": max(doc_max_file, sec_max_file),
        "largest_doc_shard_bytes": doc_max_file,
        "largest_section_shard_bytes": sec_max_file,
        "doc_plane_zlib": doc_zlib,
        "section_plane_zlib": sec_zlib,
        "zlib_growth_pct": round(100 * sec_zlib / doc_zlib, 1),
        "totality_misses": len(totality_miss),
        "totality_miss_ids": totality_miss[:20],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rungs", nargs="*", default=list(RUNGS))
    args = ap.parse_args()
    out = {}
    for name in args.rungs:
        out[name] = measure(args.ladder.expanduser() / name)
        r = out[name]
        print(f"{name}: docs {r['documents']}, multi {r['multi_section_documents']}, "
              f"sections {r['section_records']}, +{r['added_bytes']} B "
              f"({r['growth_pct']} %), largest file {r['largest_file_bytes']} B, "
              f"totality misses {r['totality_misses']}", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
