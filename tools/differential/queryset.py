"""Deterministic query-set generation for the differential harness.

**Written before the accelerator, on purpose.** A differential harness authored
after the thing it checks gets authored to pass; this one is built from the
corpus's own vocabulary by a fixed rule, so it cannot be curated toward a
green result.

Queries come from the *source documents*, not from the index — the committed
index stores 16-hex term hashes and no plaintext, so terms are unrecoverable
from it. Generating from source has the side benefit of exercising the real
`tokenize -> term_hash` path both query sides depend on.

Five sources, per the M2 design:

1. **Systematic, corpus-derived** — the whole high-`df` tail (where block
   skipping engages and where the common-term trap lives), the median band,
   and the `df == 1` singletons.
2. **Multi-term combinations** by fixed stride over the sorted vocabulary —
   rare+rare, rare+common, common+common.
3. **Hand-written goldens** supplied by the caller (fux-playground's 50).
4. **The frozen R2 questions.**
5. **Adversarial literals** — empty, stopword-only, single character, non-NFC
   unicode, a 16-hex string that looks like a term hash, and a very long
   query.

No randomness, seeded or otherwise: selection is by position in a sorted
order, so the same corpus always yields the same queries (CLAUDE.md's
determinism law applies to the harness too, or a failure is not reproducible).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fux.config import load
from fux.ingest.gitdir import walk_sources
from fux.query.tokenize import tokenize

#: The three questions frozen in the M1 handoff §9, before the engine existed.
R2_QUESTIONS = (
    "why did pruning fail",
    "what format is the committed index",
    "supersession penalty safe interval",
)

#: Shapes chosen to break a candidate generator rather than to exercise it.
ADVERSARIAL = (
    "",  # tokenizes to nothing
    "the",  # a single stopword -> still nothing
    "a the is of and",  # all stopwords
    "x",  # one character, almost certainly df == 0
    "zzzzzzzzzzzz",  # certainly df == 0
    "Å",  # non-NFC 'Å' — normalization must not diverge between paths
    "00112233445566778899aabbccddeeff",  # looks like a term hash; must not be treated as one
    "deadbeefdeadbeef",  # exactly 16 hex chars — the shape the build invariant guards
    " ".join(["index"] * 64),  # one term repeated: dedup must collapse it to a single hash
)


@dataclass(frozen=True)
class Vocabulary:
    """Every source term with its document frequency, sorted deterministically."""

    #: (term, df) sorted by df descending, then term ascending.
    by_df: list[tuple[str, int]]

    @property
    def terms(self) -> list[str]:
        return [t for t, _ in self.by_df]

    def band(self, lo: int, hi: int) -> list[str]:
        return [t for t, _ in self.by_df[lo:hi]]

    def singletons(self) -> list[str]:
        return [t for t, d in self.by_df if d == 1]


def vocabulary(root: Path) -> Vocabulary:
    """Tokenize the configured sources and count document frequency per term."""
    config = load(root)
    walked, _ = walk_sources(root, config.source_dirs)
    df: dict[str, int] = {}
    for walked_file in walked:
        for term in set(tokenize(walked_file.content.decode("utf-8"))):
            df[term] = df.get(term, 0) + 1
    return Vocabulary(by_df=sorted(df.items(), key=lambda kv: (-kv[1], kv[0])))


def generate(
    root: Path,
    *,
    common: int = 120,
    median: int = 120,
    rare: int = 120,
    pairs: int = 200,
    triples: int = 100,
    goldens: list[str] | None = None,
) -> list[str]:
    """The full query set for a corpus, deterministic and de-duplicated.

    Defaults are sized for a fast unit run over a repo-scale corpus. The lab
    raises them; the shape of the set does not change with the size.
    """
    vocab = vocabulary(root)
    total = len(vocab.by_df)
    if total == 0:
        return list(_finalize(ADVERSARIAL, R2_QUESTIONS, goldens or []))

    # 1 · the systematic bands. The high-df head is the trap B4 measured and
    # the only place block skipping can pay, so it is sampled first and hardest.
    head = vocab.band(0, min(common, total))
    mid_start = max(0, total // 2 - median // 2)
    mid = vocab.band(mid_start, mid_start + median)
    tail = vocab.singletons()[:rare] or vocab.band(max(0, total - rare), total)

    singles = [*head, *mid, *tail]

    # 2 · combinations by fixed stride — no randomness, and every pairing
    # crosses two different df bands so the rare-terms-first seeding in the
    # accelerator is exercised in both directions.
    combos: list[str] = []
    for i in range(pairs):
        a = head[i % len(head)] if head else ""
        b = tail[(i * 7) % len(tail)] if tail else ""
        combos.append(f"{b} {a}".strip())
    for i in range(pairs // 2):
        combos.append(f"{head[i % len(head)]} {head[(i * 3 + 1) % len(head)]}".strip())
    for i in range(triples):
        parts = [
            tail[(i * 5) % len(tail)] if tail else "",
            mid[(i * 11) % len(mid)] if mid else "",
            head[(i * 13) % len(head)] if head else "",
        ]
        combos.append(" ".join(p for p in parts if p).strip())

    return list(_finalize(singles, combos, ADVERSARIAL, R2_QUESTIONS, goldens or []))


def _finalize(*groups) -> list[str]:
    """Concatenate, drop duplicates, preserve first-seen order."""
    seen: dict[str, None] = {}
    for group in groups:
        for query in group:
            seen.setdefault(query, None)
    return list(seen)
