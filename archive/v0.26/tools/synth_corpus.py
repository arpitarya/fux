"""Generate a synthetic documentation corpus for the scale benchmark (M8).

    uv run python tools/synth_corpus.py --docs 100000 --out /tmp/synth-100k

Committed because a benchmark you cannot reproduce is an anecdote. Everything
here is seeded and deterministic: the same `--docs` and `--seed` produce
byte-identical files on any machine, so a number measured today can be
re-measured against tomorrow's engine.

**What it models, and why.** A corpus that is only random words would flatter
the engine — BM25F would see uniform statistics and the graph would be empty.
This generator deliberately reproduces the properties that make retrieval hard
and make the measurements meaningful:

- **Zipfian vocabulary** — a few very common terms and a long tail, so `df`
  varies across four orders of magnitude the way real prose does.
- **Real link structure** — every document links to neighbours, cites a few
  others, and carries tags. Without this, PPR expansion has nothing to walk,
  which is exactly what made the 9-document fixture unable to decide handoff
  open question 2 at M6.
- **Heading hierarchy** — so the heading field carries weight and the chunker
  has real structure to split on.
- **A skewed size distribution** — most documents short, a few long, because
  a uniform corpus hides the length-normalization term.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

# A small closed vocabulary sampled Zipfian: realistic df spread without
# needing a word list dependency.
TOPICS = [
    "payments", "ledger", "settlement", "reconciliation", "idempotency",
    "webhook", "retry", "backoff", "throughput", "latency", "shard", "replica",
    "failover", "rollback", "canary", "telemetry", "tracing", "quota",
    "tenancy", "encryption", "rotation", "audit", "retention", "schema",
    "migration", "index", "partition", "checkpoint", "snapshot", "compaction",
]
VERBS = ["records", "rejects", "retries", "batches", "streams", "validates",
         "reconciles", "escalates", "throttles", "replicates"]
NOUNS = ["service", "pipeline", "queue", "gateway", "worker", "store",
         "cluster", "endpoint", "contract", "runbook"]


def zipf_pick(rng: random.Random, items: list[str]) -> str:
    """Rank-biased choice: item i is picked ~1/(i+1) as often as the first."""
    weights = [1.0 / (i + 1) for i in range(len(items))]
    return rng.choices(items, weights=weights, k=1)[0]


def paragraph(rng: random.Random, topic: str) -> str:
    sentences = []
    for _ in range(rng.randint(2, 5)):
        sentences.append(
            f"The {topic} {zipf_pick(rng, NOUNS)} {zipf_pick(rng, VERBS)} "
            f"{zipf_pick(rng, TOPICS)} across every {zipf_pick(rng, NOUNS)}."
        )
    return " ".join(sentences)


def make_doc(index: int, total: int, rng: random.Random) -> tuple[str, str]:
    topic = TOPICS[index % len(TOPICS)]
    secondary = zipf_pick(rng, TOPICS)
    # Skewed length: most docs short, a long tail of big ones.
    sections = rng.choice([2, 2, 3, 3, 4, 6, 10])

    neighbours = sorted({
        (index + offset) % total
        for offset in (1, 3, 7, rng.randint(1, max(2, total // 10)))
        if (index + offset) % total != index
    })
    cited = sorted({(index * 7 + k) % total for k in (2, 5)} - {index})

    lines = [
        "---",
        f"title: {topic.title()} {zipf_pick(rng, NOUNS)} {index:06d}",
        f"tags: [{topic}, {secondary}]",
        "---",
        f"# {topic.title()} {index:06d}",
        "",
        paragraph(rng, topic),
        "",
    ]
    for section in range(sections):
        lines += [
            f"## {zipf_pick(rng, TOPICS).title()} {section}",
            "",
            paragraph(rng, topic),
            "",
        ]
    if neighbours:
        lines += ["## See also", ""]
        lines += [f"- [{n:06d}](doc-{n:06d}.md)" for n in neighbours]
        lines += [""]
    if cited:
        lines += ["## Citations", ""]
        lines += [f"- [{c:06d}](doc-{c:06d}.md)" for c in cited]
        lines += [""]
    return f"doc-{index:06d}.md", "\n".join(lines)


def generate(out: Path, docs: int, seed: int) -> tuple[int, int]:
    corpus = out / "docs"
    corpus.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    for index in range(docs):
        rng = random.Random(f"{seed}:{index}")  # per-doc seed: order-independent
        name, text = make_doc(index, docs, rng)
        data = text.encode("utf-8")
        (corpus / name).write_bytes(data)
        total_bytes += len(data)
    (out / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n\n[index]\nformat = "sqlite"\n', encoding="utf-8"
    )
    return docs, total_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=int, default=100_000)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    docs, total = generate(args.out, args.docs, args.seed)
    print(f"generated {docs} docs · {total / 1e6:.1f} MB source · {args.out}")
    print(f"avg {total / docs:.0f} B/doc")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
