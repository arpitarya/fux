"""Fork 3's measurement: what per-field extrema cost the block bound.

**The question.** W-76 Phase 1 made the field weights tunable at query time,
which forced the accelerator's `mx` / `mnw` from pre-weighted scalars to
per-field arrays recombined at query time. That recombination is provably
safe — both errors push the bound UP, so no document is ever lost — but a
looser bound skips fewer blocks, and nobody had measured how many.

**The bar.** R3: warm p95 <= 150 ms. The measured pre-change figure was
27.2 ms on 8 870 RFC documents, so there is roughly 5x of headroom. "There is
headroom" is not a measurement, which is why this file exists.

**What is reported**, at the 10 000-document design-point ceiling:

1. warm p95 for the accelerator, against the 150 ms bar
2. the reference scan's p95, for scale
3. **blocks read with per-field extrema vs. with an oracle scalar bound** —
   the pruning loss attributable to fork 3 specifically, isolated from
   everything else that changed in Phase 1

(3) is the number that actually answers the fork. A p95 inside the bar with
90 % more blocks read is a different situation from one with 5 % more.
"""

from __future__ import annotations

import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fux.derive import accel, build  # noqa: E402
from fux.derive.accel import Runtime  # noqa: E402
from fux.query import scan  # noqa: E402
from fux.query.scan import query_term_hashes  # noqa: E402

VOCAB = [
    "retry", "backoff", "jitter", "payments", "storage", "engine", "index",
    "committed", "shard", "posting", "accelerator", "differential", "bound",
    "analyzer", "stemming", "identifier", "throughput", "latency", "cache",
    "invalidation", "rollback", "runbook", "oncall", "escalation", "quorum",
    "replication", "partition", "consensus", "checkpoint", "compaction",
]
IDENTIFIERS = [
    "getUserName", "parseRequestBody", "HTTPRetryPolicy", "shard_for_document",
    "BM25F", "computeBlockBound", "flushWriteAheadLog", "SHA256",
]


def make_corpus(root: Path, n_docs: int, seed: int = 20260823) -> None:
    rng = random.Random(seed)
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    sources = root / ".fux" / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    (sources / "dirs").write_text("docs\n", encoding="utf-8")

    for i in range(n_docs):
        topic = rng.sample(VOCAB, k=rng.randint(3, 8))
        ident = rng.choice(IDENTIFIERS)
        # Zipf-ish body: a few terms dominate, most are rare. A uniform corpus
        # makes every block bound equally tight and hides exactly the effect
        # this benchmark exists to measure.
        body_terms = rng.choices(VOCAB, k=rng.randint(80, 400))
        section = rng.choice(["Design", "Operations", "Rationale", "Rollout"])
        (docs / f"note-{i:05d}.md").write_text(
            f"# {' '.join(topic[:3]).title()}\n\n"
            f"The {ident} path covers {', '.join(topic)}.\n\n"
            f"## {section}\n\n" + " ".join(body_terms) + "\n",
            encoding="utf-8",
        )


def queries(rng: random.Random, k: int = 60) -> list[str]:
    out = []
    for _ in range(k):
        n = rng.choice([1, 2, 2, 3])
        out.append(" ".join(rng.sample(VOCAB, k=n)))
    return out


def blocks_read(runtime: Runtime, query: str, top: int) -> int:
    """How many blocks the accelerator actually parses for one query."""
    hashes = query_term_hashes(query)
    if not hashes:
        return 0
    seen = 0
    original = runtime.read_block

    def counting(block):
        nonlocal seen
        seen += 1
        return original(block)

    runtime.read_block = counting  # type: ignore[method-assign]
    try:
        accel.accel_candidates(runtime, hashes, top, skipping=True)
    finally:
        runtime.read_block = original  # type: ignore[method-assign]
    return seen


def blocks_read_with_tight_bound(runtime: Runtime, query: str, top: int) -> int:
    """Blocks read if the bound were the PRE-fork-3 tight scalar.

    The attribution measurement. A p95 inside the bar says the system is fast
    enough; it does not say what the looser bound cost, because the corpus and
    the machine differ from every earlier run. This computes the tight bound —
    the block's true maximum weighted tf and true minimum weighted length,
    read from the block's own postings — and counts blocks read under it, on
    the same corpus, in the same process, in the same second.

    The difference between the two counts is fork 3's real price.
    """
    from fux.query.bm25f import FIELD_WEIGHTS, K1, B, idf, weighted_tf, derive_wlen

    def tight(block, df, n, avg_wlen, weights=FIELD_WEIGHTS):
        postings = original_read(block)
        wtf = max((weighted_tf(tf, weights) for _, tf in postings), default=0.0)
        if wtf == 0:
            return 0.0
        mnw = min(
            (derive_wlen(runtime.docs[docidx]["flen"], weights) for docidx, _ in postings),
            default=0.0,
        )
        denom = wtf + K1 * (1 - B + B * mnw / avg_wlen)
        return idf(df, n) * wtf * (K1 + 1) / denom

    hashes = query_term_hashes(query)
    if not hashes:
        return 0
    seen = 0
    original_read = runtime.read_block

    def counting(block):
        nonlocal seen
        seen += 1
        return original_read(block)

    runtime.read_block = counting  # type: ignore[method-assign]
    real_bound = accel.block_bound
    accel.block_bound = tight  # type: ignore[assignment]
    try:
        accel.accel_candidates(runtime, hashes, top, skipping=True)
    finally:
        runtime.read_block = original_read  # type: ignore[method-assign]
        accel.block_bound = real_bound  # type: ignore[assignment]
    return seen


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * 0.95) - 1)]


def main() -> int:
    n_docs = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/fork3corpus")

    if not (root / ".fux" / "index").exists():
        print(f"building a {n_docs}-document corpus at {root} ...", flush=True)
        make_corpus(root, n_docs)
        from fux.ingest.run import run as ingest

        t0 = time.perf_counter()
        ingest(root)
        print(f"  ingest: {time.perf_counter() - t0:.1f} s", flush=True)
        t0 = time.perf_counter()
        build(root)
        print(f"  build:  {time.perf_counter() - t0:.1f} s", flush=True)

    rng = random.Random(1)
    qs = queries(rng)
    runtime = Runtime(root)

    for q in qs[:5]:  # warm caches
        accel.ask(root, q, top=5)

    accel_ms, scan_ms, blocks, tight_blocks = [], [], [], []
    for q in qs:
        for top in (5, 20):
            t0 = time.perf_counter()
            accel.ask(root, q, top=top)
            accel_ms.append((time.perf_counter() - t0) * 1000)
            blocks.append(blocks_read(runtime, q, top))
            tight_blocks.append(blocks_read_with_tight_bound(runtime, q, top))

    for q in qs[:12]:  # the scan is slow; a smaller sample is enough for scale
        t0 = time.perf_counter()
        scan.ask(root, q, top=5)
        scan_ms.append((time.perf_counter() - t0) * 1000)

    print()
    print(f"corpus                 {n_docs} documents")
    print(f"queries                {len(qs)} x 2 tops = {len(accel_ms)} timed calls")
    print(f"accelerator p95        {p95(accel_ms):8.2f} ms   (bar: 150 ms)")
    print(f"accelerator median     {statistics.median(accel_ms):8.2f} ms")
    print(f"reference scan p95     {p95(scan_ms):8.2f} ms")
    print(f"blocks read, median    {statistics.median(blocks):8.1f}")
    print(f"blocks read, p95       {p95([float(b) for b in blocks]):8.1f}")
    loose_total, tight_total = sum(blocks), sum(tight_blocks)
    extra = (loose_total / tight_total - 1) * 100 if tight_total else 0.0
    print()
    print("--- fork 3 attribution, same corpus and process ---")
    print(f"blocks read, per-field (loose)   {loose_total:8d}")
    print(f"blocks read, oracle    (tight)   {tight_total:8d}")
    print(f"extra blocks read attributable to fork 3   {extra:+.1f} %")

    verdict = "PASS" if p95(accel_ms) <= 150 else "FAIL"
    print(f"\nR3 bar (150 ms warm p95): {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
