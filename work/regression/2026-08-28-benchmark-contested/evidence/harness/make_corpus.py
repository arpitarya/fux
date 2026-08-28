#!/usr/bin/env python3
"""Generate a deterministic synthetic documentation corpus, plus eval pairs.

**Seeded and byte-identical for the same `--seed` and `--docs`.** A measurement
over a corpus nobody can regenerate is a measurement nobody can check — which
is exactly the position the lab was left in when it vanished with its corpora
(fux W-56). TEST-PLAN §5.

Stdlib only, deliberately: the engine under test carries no third-party runtime
dependency, and a harness that needs numpy to measure a `$0` tool is a harness
that cannot run wherever the tool can.

## What it emits

```
<out>/repo/docs/<area>/<kind>-<n>.md     the corpus
<out>/eval/pairs.jsonl                   {"q": ..., "doc": ...} one per line
```

Every document carries frontmatter, one `#` title and two or three `##`
sections, so the extractor has headings to mine and the chunker has boundaries
to find.

## Why the pairs are constructed, not sampled

Each eval pair names a **rare term** planted in exactly one document. That
makes the expected answer unambiguous without a human grading anything — which
is the honest limit of a generated corpus, and the reason this is the *lab* and
not the playground. **A generated pair measures retrieval mechanics; it does
not measure whether an answer is good.**

## Bench mode (`--bench`) — three planted structures the plain mode has not got

`--bench` emits the same corpus shape plus the structures a **version-to-version
benchmark** needs, and three more eval files beside `pairs.jsonl`:

```
<out>/eval/chains.jsonl        {"q", "current", "superseded"}   supersession inversions
<out>/eval/unanswerable.jsonl  {"q", "kind"}                    honest-decline probes
<out>/eval/decoys.jsonl        {"q", "decoy", "target"}         the placebo control
<out>/eval/contested.jsonl     {"q", "kind", "target", ...}     contested answers
<out>/eval/manifest.json       every document's planted role
```

- **Supersession chains.** Two documents carry the *same* rare marker; the newer
  one declares `supersedes: [<path of the older>]` in frontmatter. An
  **inversion** is the retired document outranking its successor. ⚠ **The two
  are given unrelated document numbers and their old/new roles are drawn from
  the seeded stream**, so lexicographic order does not correlate with currency —
  otherwise an engine that breaks ties by path would score 0 % or 100 %
  inversions and the number would be measuring `sorted()`.
- **Decoys.** Topically adjacent, factually silent: same area, same topic
  vocabulary, the same *"The … procedure applies here."* sentence shape, and
  **no rare marker anywhere**. A decoy in the top-`k` for a marker query is a
  false positive nothing in the plain corpus could catch.
- **Unanswerables**, in two kinds, because they fail differently:
  `absent-entity` queries a marker planted in **no** document;
  `compositional` uses only vocabulary the corpus does have, in a combination
  no single document carries.

## Contested answers (`--contested`, `--field`) — and why they had to exist

🔴 **A marker query cannot detect a ranking change, and the 2026-08-28 version
benchmark is the measurement that proves it.** `hit@5` came back **240/240 in
both arms at every tier**: a term planted in exactly one document has `df = 1`,
is already rank 1, and no reranker can move it up or break it. In McNemar's
terms `pb` and `pc` are **structurally zero** — the discordant count was fixed
by the corpus before either engine ran. The set was sized correctly by a power
table and still could not detect anything, because **a power table says how many
queries; it never says whether the queries are HARD** (fux W-95).

A contested cluster is the fix. `--cluster` candidates share the query's terms
**at equal term frequency, equal field and equal length**; exactly one is the
declared target, and it is distinguished by a single property:

| kind | every candidate has | only the target has | the lane it exercises |
|---|---|---|---|
| `proximity` | marker `a` once, marker `b` once, in two fixed-shape sentences | the two markers in the **same sentence** | the proximity reranker |
| `path` | the marker exactly once | it in the **filename**, and in no prose | the `path` tf field |
| `heading` | the marker exactly once | it as **heading text**, not body prose | a **negative control** |

⚠ **`heading` is a control, and that is its whole job.** `1.0.0` and `HEAD`
both weight `heading` 3.0 against `body` 1.0, so the two arms are identical here
by construction and the endpoint must return a null. A delta on `heading` means
the instrument is measuring something other than the field it names.

**Both markers have `df = cluster`, so no candidate wins on rarity**, and a
bag-of-words ranker sees the same evidence in all of them. `--selftest` asserts
that: equal `tf` in every candidate, exactly one candidate carrying the
distinguishing property, and the target's path order uncorrelated with its role
— the same tie-break guard the chains carry, because near-identical candidates
are exactly where an engine ordering ties by path would score 0 % or 100 %.

⚠ **The honest limit of a contested query, stated up front.** The base documents
state no facts, so "correct" here is **declared by construction, not true**. The
proximity suite measures whether an engine prefers a document where the queried
terms *co-occur* — which is what a two-concept question usually wants — and the
field suite whether it prefers a heading match. Neither measures whether the
retrieved document answers anything. That remains the standing limit of a
generated corpus and the reason the playground exists.

⚠ **The honest limit, stated here rather than discovered later.** On a
generated corpus *"unanswerable"* means **no document holds the queried
marker** — not *"no true answer exists"*. The base documents are drawn from a
closed vocabulary and state no facts at all, so this instrument can show that an
answer layer **declines when nothing matches**; it cannot show that it declines
when something matches but does not support the claim.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

AREAS = ("platform", "storage", "network", "identity", "billing")
KINDS = ("adr", "runbook", "guide", "postmortem", "reference")

# A closed vocabulary, so document frequency is a property of the generator
# rather than of whatever words happened to come to mind.
COMMON = (
    "service deploy request latency cluster region rollout config release "
    "queue retry timeout traffic client server index cache shard replica "
    "policy access token audit log metric alert dashboard threshold"
).split()

TOPIC = {
    "platform": "scheduler autoscaler namespace workload container".split(),
    "storage": "volume snapshot durability throughput compaction".split(),
    "network": "ingress egress peering bandwidth firewall".split(),
    "identity": "principal credential rotation federation scope".split(),
    "billing": "invoice proration ledger settlement chargeback".split(),
}


def _sentence(rng: random.Random, words: list[str], n: int) -> str:
    return " ".join(rng.choice(words) for _ in range(n)).capitalize() + "."


def _document(
    rng: random.Random,
    area: str,
    kind: str,
    n: int,
    rare: str | None,
    *,
    extra_rares: tuple[str, ...] = (),
    supersedes: str | None = None,
) -> str:
    """One document. `rare` is the legacy single marker; `extra_rares` adds more.

    ⚠ **`extra_rares` and `supersedes` consume no random draws when empty**, so
    a corpus generated by the plain path is byte-identical to the one this file
    produced before bench mode existed. That property is asserted by
    `--selftest`, not merely intended.
    """
    words = COMMON + TOPIC[area]
    title = f"{kind.capitalize()} {n}: {area} {rng.choice(TOPIC[area])}"
    head = [f"title: {title}", f"tags: [{area}, {kind}]"]
    if supersedes:
        head.append(f"supersedes: [{supersedes}]")
    out = ["---\n" + "\n".join(head) + "\n---", f"# {title}", ""]

    # The rare term goes in the body of the first section, never the title —
    # a term that only ever appears in a heading measures the heading weight,
    # not retrieval.
    sections = rng.randint(2, 3)
    for s in range(sections):
        out.append(f"## {rng.choice(TOPIC[area]).capitalize()} {s + 1}")
        out.append("")
        body = [_sentence(rng, words, rng.randint(8, 18)) for _ in range(rng.randint(2, 5))]
        if rare and s == 0:
            body.insert(rng.randrange(len(body) + 1), f"The {rare} procedure applies here.")
        for marker in extra_rares:
            body.insert(rng.randrange(len(body) + 1), f"The {marker} procedure applies here.")
        out.append(" ".join(body))
        out.append("")
    return "\n".join(out)


def generate(out: Path, docs: int, seed: int) -> dict:
    rng = random.Random(seed)
    repo = out / "repo"
    evaldir = out / "eval"
    (evaldir).mkdir(parents=True, exist_ok=True)

    pairs: list[dict] = []
    written = 0
    for i in range(docs):
        area = AREAS[i % len(AREAS)]
        kind = KINDS[(i // len(AREAS)) % len(KINDS)]
        # One in eight documents gets a unique rare term and an eval pair.
        rare = f"zx{i:05d}q" if i % 8 == 0 else None
        rel = Path("docs") / area / f"{kind}-{i:05d}.md"
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_document(rng, area, kind, i, rare), encoding="utf-8")
        written += 1
        if rare:
            pairs.append({"q": f"{rare} procedure", "doc": rel.as_posix()})

    (evaldir / "pairs.jsonl").write_text(
        "".join(json.dumps(p, sort_keys=True) + "\n" for p in pairs), encoding="utf-8"
    )
    return {"docs": written, "pairs": len(pairs), "seed": seed}


# ---------------------------------------------------------------------------
# Bench mode — the three planted structures a version comparison needs.
# ---------------------------------------------------------------------------

#: Marker prefixes. Kept distinct so a grep can prove an "unanswerable" query's
#: term really is absent from the corpus — `zq` is planted in NO document, ever.
PLANTED_PREFIX = "zx"
CHAIN_PREFIX = "zc"
ABSENT_PREFIX = "zq"

#: Contested-answer markers. Unlike `zx`, whose `df = 1` is exactly what made
#: the marker suite unable to detect a ranking change at all, these are planted
#: in EVERY candidate of a cluster, so no candidate wins on term rarity.
#: `zp` — proximity.  `zh` — heading field.  `zn` — path field.
CONTEST_PREFIX = "zp"
HEADING_PREFIX = "zh"
PATH_PREFIX = "zn"

#: Every planted sentence in a contested cluster has this shape and this word
#: count. Holding the shape constant is what makes "the only difference is the
#: property under test" a checkable claim rather than an intention.
_MARK_TAIL = "procedure applies here."
#: Fixed body shape for cluster members: N sections x M sentences x W words.
_CONTEST_SECTIONS = 3
_CONTEST_FILLER = 3
_CONTEST_FILLER_WORDS = 12


def _plan(
    docs: int,
    chains: int,
    decoys: int,
    rng: random.Random,
    contested: int = 0,
    heading: int = 0,
    pathc: int = 0,
    cluster: int = 4,
) -> dict:
    """Assign every document slot a role, before a byte is written.

    Roles are drawn from `rng` rather than from the index, so a chain's old and
    new halves get **unrelated document numbers** — see the module docstring.
    """
    slots = list(range(docs))
    rng.shuffle(slots)

    need = chains * 2 + decoys + (contested + heading + pathc) * cluster
    if need > docs:  # pragma: no cover - guarded by the caller
        raise SystemExit(f"cannot plant {need} special docs in a {docs}-doc corpus")

    cur = 0
    chain_slots = [(slots[cur + 2 * i], slots[cur + 2 * i + 1]) for i in range(chains)]
    cur += chains * 2
    decoy_slots = slots[cur : cur + decoys]
    cur += decoys
    # A cluster's members get UNRELATED document numbers, drawn from the shuffled
    # stream — the same guard the chains carry. Candidates in a contest are near
    # enough identical that an engine breaking ties by path would otherwise score
    # 0 % or 100 %, and the number would be measuring `sorted()`.
    contest_slots = [
        slots[cur + cluster * i : cur + cluster * (i + 1)] for i in range(contested)
    ]
    cur += contested * cluster
    heading_slots = [
        slots[cur + cluster * i : cur + cluster * (i + 1)] for i in range(heading)
    ]
    cur += heading * cluster
    path_slots = [
        slots[cur + cluster * i : cur + cluster * (i + 1)] for i in range(pathc)
    ]
    cur += pathc * cluster
    base_slots = sorted(slots[cur:])
    return {
        "chains": chain_slots,
        "decoys": decoy_slots,
        "contested": contest_slots,
        "heading": heading_slots,
        "path": path_slots,
        "base": base_slots,
    }


def _area_kind(i: int) -> tuple[str, str]:
    return AREAS[i % len(AREAS)], KINDS[(i // len(AREAS)) % len(KINDS)]


def _rel(i: int) -> Path:
    area, kind = _area_kind(i)
    return Path("docs") / area / f"{kind}-{i:05d}.md"


def _decoy_document(rng: random.Random, area: str, kind: str, n: int) -> str:
    """Topically adjacent, factually silent.

    It carries the marker SENTENCE — *"The … procedure applies here."* — with a
    common word where the marker would be, so it competes on every term of a
    marker query except the one that matters. **No `zx`/`zc` token anywhere.**
    """
    words = COMMON + TOPIC[area]
    title = f"{kind.capitalize()} {n}: {area} {rng.choice(TOPIC[area])}"
    out = [f"---\ntitle: {title}\ntags: [{area}, {kind}]\n---", f"# {title}", ""]
    sections = rng.randint(2, 3)
    for s in range(sections):
        out.append(f"## {rng.choice(TOPIC[area]).capitalize()} {s + 1}")
        out.append("")
        body = [_sentence(rng, words, rng.randint(8, 18)) for _ in range(rng.randint(2, 5))]
        if s == 0:
            body.insert(
                rng.randrange(len(body) + 1),
                f"The {rng.choice(TOPIC[area])} procedure applies here.",
            )
        out.append(" ".join(body))
        out.append("")
    return "\n".join(out)


def _mark_sentence(x: str, y: str) -> str:
    """Always six words: `The <x> <y> procedure applies here.`

    Two slots, always filled. A target and a distractor therefore differ in
    WHICH tokens sit in the slots and never in how many tokens there are.
    """
    return f"The {x} {y} {_MARK_TAIL}"


def _contest_body(
    rng: random.Random,
    area: str,
    kind: str,
    n: int,
    marks: list[tuple[int, str]],
    *,
    heading_marker: str | None = None,
    heading_section: int = 0,
) -> str:
    """One cluster candidate, built to a FIXED shape.

    Section count, sentence count and sentence length are constants here, not
    draws, so two candidates of the same cluster have the same length to within
    the vocabulary. Length normalisation therefore cannot prefer one candidate
    over another, which is the confound that would otherwise let a target win
    for a reason that has nothing to do with the property under test.

    `marks` is `(section index, sentence)` — the planted sentences, appended
    after the filler so their position in the section is also constant.
    """
    words = COMMON + TOPIC[area]
    title = f"{kind.capitalize()} {n}: {area} {rng.choice(TOPIC[area])}"
    out = [f"---\ntitle: {title}\ntags: [{area}, {kind}]\n---", f"# {title}", ""]
    by_section: dict[int, list[str]] = {}
    for s, sentence in marks:
        by_section.setdefault(s, []).append(sentence)
    for s in range(_CONTEST_SECTIONS):
        # The heading is a field, and the field contest is decided here: the
        # target carries the marker as heading text where the distractors carry
        # an ordinary topic word. Same token count either way.
        if heading_marker and s == heading_section:
            # NOT capitalised: the marker is the token under test, and a
            # heading that title-cased it would leave the raw corpus carrying a
            # different string than the query does. The analyzer folds case, so
            # this changes no score — it keeps the planted fact greppable,
            # which is what makes `--selftest` able to check it at all.
            head = heading_marker
        else:
            head = rng.choice(TOPIC[area]).capitalize()
        out.append(f"## {head} {s + 1}")
        out.append("")
        body = [
            _sentence(rng, words, _CONTEST_FILLER_WORDS) for _ in range(_CONTEST_FILLER)
        ]
        body.extend(by_section.get(s, []))
        out.append(" ".join(body))
        out.append("")
    return "\n".join(out)


def _unanswerables(rng: random.Random, count: int) -> list[dict]:
    """Half absent-entity, half compositional. They fail differently."""
    out: list[dict] = []
    for i in range(count):
        if i % 2 == 0:
            out.append({"q": f"{ABSENT_PREFIX}{i:05d}w procedure", "kind": "absent-entity"})
        else:
            area = AREAS[i % len(AREAS)]
            kind = KINDS[i % len(KINDS)]
            a, b = rng.sample(TOPIC[area], 2)
            out.append(
                {
                    "q": f"which {a} does the {area} {kind} {b} rollout require",
                    "kind": "compositional",
                }
            )
    return out


def generate_bench(
    out: Path,
    docs: int,
    seed: int,
    pairs_target: int,
    chains: int,
    decoys: int,
    unanswerable: int,
    contested: int = 0,
    heading: int = 0,
    pathc: int = 0,
    cluster: int = 4,
) -> dict:
    """The bench corpus. Same seed and same counts -> byte-identical bytes."""
    rng = random.Random(seed)
    repo = out / "repo"
    evaldir = out / "eval"
    evaldir.mkdir(parents=True, exist_ok=True)

    budget = docs - decoys - (contested + heading + pathc) * cluster
    chains = min(chains, max(0, budget // 2))
    plan = _plan(docs, chains, decoys, rng, contested, heading, pathc, cluster)
    manifest: dict[str, str] = {}

    # --- chains ------------------------------------------------------------
    chain_rows: list[dict] = []
    for c, (x, y) in enumerate(plan["chains"]):
        marker = f"{CHAIN_PREFIX}{c:05d}a"
        # Which half is the retired one is a coin flip from the seeded stream,
        # so path order carries no information about currency.
        old_i, new_i = (x, y) if rng.random() < 0.5 else (y, x)
        old_rel, new_rel = _rel(old_i), _rel(new_i)
        for i, rel, sup in ((old_i, old_rel, None), (new_i, new_rel, old_rel.as_posix())):
            area, kind = _area_kind(i)
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                _document(rng, area, kind, i, marker, supersedes=sup), encoding="utf-8"
            )
            manifest[rel.as_posix()] = "chain-new" if sup else "chain-old"
        chain_rows.append(
            {
                "q": f"{marker} procedure",
                "current": new_rel.as_posix(),
                "superseded": old_rel.as_posix(),
            }
        )

    # --- contested answers: the PROXIMITY contest --------------------------
    # Every candidate carries marker `a` once and marker `b` once, in two
    # sentences of identical shape. Only the target has them in the SAME
    # sentence. Term frequency, field and length are equal across the cluster,
    # so a bag-of-words ranker has nothing to prefer the target ON — which is
    # precisely the headroom the marker suite does not have.
    contest_rows: list[dict] = []
    for c, members in enumerate(plan["contested"]):
        a, b = f"{CONTEST_PREFIX}{c:05d}a", f"{CONTEST_PREFIX}{c:05d}b"
        target_at = rng.randrange(len(members))
        rels = [_rel(i) for i in members]
        for j, i in enumerate(members):
            area, kind = _area_kind(i)
            c1, c2 = rng.sample(COMMON, 2)
            if j == target_at:
                marks = [(0, _mark_sentence(a, b)), (_CONTEST_SECTIONS - 1, _mark_sentence(c1, c2))]
            else:
                marks = [(0, _mark_sentence(a, c1)), (_CONTEST_SECTIONS - 1, _mark_sentence(b, c2))]
            path = repo / rels[j]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_contest_body(rng, area, kind, i, marks), encoding="utf-8")
            manifest[rels[j].as_posix()] = "contest-target" if j == target_at else "contest-distractor"
        contest_rows.append({
            "q": f"{a} {b} procedure",
            "kind": "proximity",
            "target": rels[target_at].as_posix(),
            "candidates": sorted(r.as_posix() for r in rels),
        })

    # --- contested answers: the HEADING field — a NEGATIVE control ---------
    # Arm A weights `heading` 3.0 and `body` 1.0. Arm B weights them the SAME.
    # So this contest is decided by a field both engines already have, and it
    # exists to return a null: if a version delta shows up here, the instrument
    # is measuring something other than the field it names.
    for c, members in enumerate(plan["heading"]):
        m = f"{HEADING_PREFIX}{c:05d}a"
        target_at = rng.randrange(len(members))
        rels = [_rel(i) for i in members]
        for j, i in enumerate(members):
            area, kind = _area_kind(i)
            c1, c2 = rng.sample(COMMON, 2)
            if j == target_at:
                body = _contest_body(rng, area, kind, i, [(0, _mark_sentence(c1, c2))],
                                     heading_marker=m, heading_section=0)
            else:
                body = _contest_body(rng, area, kind, i, [(0, _mark_sentence(m, c2))])
            path = repo / rels[j]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            manifest[rels[j].as_posix()] = "heading-target" if j == target_at else "heading-distractor"
        contest_rows.append({
            "q": f"{m} procedure", "kind": "heading",
            "target": rels[target_at].as_posix(),
            "candidates": sorted(r.as_posix() for r in rels),
        })

    # --- contested answers: the PATH field — the version discriminator ------
    # 🔴 This is the one contest whose deciding field exists in ONE arm only.
    # `1.0.0` commits two tf fields (`body`, `heading`); `HEAD` commits five and
    # weights `path` at 1.5. The marker appears in the TARGET'S FILENAME and
    # nowhere in its prose; in every distractor it appears once in prose and
    # never in the filename. An engine with no path field cannot see the target
    # at all on this term — and, unlike the priors, five committed fields are
    # structural: there is no knob that ships them off.
    for c, members in enumerate(plan["path"]):
        m = f"{PATH_PREFIX}{c:05d}a"
        target_at = rng.randrange(len(members))
        rels = []
        for j, i in enumerate(members):
            area, kind = _area_kind(i)
            if j == target_at:
                rels.append(Path("docs") / area / f"{kind}-{m}-{i:05d}.md")
            else:
                rels.append(_rel(i))
        for j, i in enumerate(members):
            area, kind = _area_kind(i)
            c1, c2 = rng.sample(COMMON, 2)
            marks = [(0, _mark_sentence(c1, c2))] if j == target_at else [(0, _mark_sentence(m, c2))]
            path = repo / rels[j]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_contest_body(rng, area, kind, i, marks), encoding="utf-8")
            manifest[rels[j].as_posix()] = "path-target" if j == target_at else "path-distractor"
        contest_rows.append({
            "q": f"{m} procedure", "kind": "path",
            "target": rels[target_at].as_posix(),
            "candidates": sorted(r.as_posix() for r in rels),
        })

    # --- base documents and their markers ----------------------------------
    base = plan["base"]
    pair_rows: list[dict] = []
    per_doc: dict[int, list[str]] = {i: [] for i in base}
    if base:
        for k in range(pairs_target):
            per_doc[base[k % len(base)]].append(f"{PLANTED_PREFIX}{k:05d}q")
    for i in base:
        area, kind = _area_kind(i)
        rel = _rel(i)
        markers = per_doc[i]
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _document(
                rng,
                area,
                kind,
                i,
                markers[0] if markers else None,
                extra_rares=tuple(markers[1:]),
            ),
            encoding="utf-8",
        )
        manifest[rel.as_posix()] = "base-marked" if markers else "base"
        for m in markers:
            pair_rows.append({"doc": rel.as_posix(), "q": f"{m} procedure"})

    # --- decoys ------------------------------------------------------------
    decoy_rows: list[dict] = []
    pair_by_area: dict[str, list[dict]] = {}
    for row in pair_rows:
        pair_by_area.setdefault(Path(row["doc"]).parent.name, []).append(row)
    for d, i in enumerate(sorted(plan["decoys"])):
        area, kind = _area_kind(i)
        rel = _rel(i)
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_decoy_document(rng, area, kind, i), encoding="utf-8")
        manifest[rel.as_posix()] = "decoy"
        shadowed = pair_by_area.get(area) or pair_rows
        if shadowed:
            target = shadowed[d % len(shadowed)]
            decoy_rows.append(
                {"q": target["q"], "decoy": rel.as_posix(), "target": target["doc"]}
            )

    unans = _unanswerables(rng, unanswerable)

    def _write(name: str, rows: list[dict]) -> None:
        (evaldir / name).write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
        )

    pair_rows.sort(key=lambda r: r["q"])
    chain_rows.sort(key=lambda r: r["q"])
    decoy_rows.sort(key=lambda r: (r["q"], r["decoy"]))
    contest_rows.sort(key=lambda r: r["q"])
    _write("pairs.jsonl", pair_rows)
    _write("chains.jsonl", chain_rows)
    _write("decoys.jsonl", decoy_rows)
    _write("unanswerable.jsonl", unans)
    _write("contested.jsonl", contest_rows)
    (evaldir / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )

    return {
        "docs": len(manifest),
        "pairs": len(pair_rows),
        "chains": len(chain_rows),
        "decoys": len(decoy_rows),
        "unanswerable": len(unans),
        "contested": sum(1 for r in contest_rows if r["kind"] == "proximity"),
        "heading": sum(1 for r in contest_rows if r["kind"] == "heading"),
        "path": sum(1 for r in contest_rows if r["kind"] == "path"),
        "cluster": cluster,
        "seed": seed,
    }


def _selftest() -> int:
    """Two properties worth more than a comment, checked before every run."""
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="make-corpus-selftest-"))
    try:
        a, b = tmp / "a", tmp / "b"
        generate_bench(a, 260, 3, 60, 8, 6, 10, contested=8, heading=6, pathc=6, cluster=4)
        generate_bench(b, 260, 3, 60, 8, 6, 10, contested=8, heading=6, pathc=6, cluster=4)
        for left in sorted(a.rglob("*")):
            if left.is_file():
                right = b / left.relative_to(a)
                assert left.read_bytes() == right.read_bytes(), f"nondeterministic: {left}"

        # No `zq` marker may appear in any document — an "unanswerable" whose
        # term is quietly planted is a query that measures nothing.
        for doc in (a / "repo").rglob("*.md"):
            text = doc.read_text(encoding="utf-8")
            assert ABSENT_PREFIX not in text, f"{doc} carries an absent-entity marker"

        # A decoy carries no marker of any kind.
        manifest = json.loads((a / "eval" / "manifest.json").read_text(encoding="utf-8"))
        for rel, role in manifest.items():
            if role == "decoy":
                text = (a / "repo" / rel).read_text(encoding="utf-8")
                assert PLANTED_PREFIX not in text and CHAIN_PREFIX not in text, rel

        # Every chain's newer half declares the older one.
        for row in (a / "eval" / "chains.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(row)
            text = (a / "repo" / r["current"]).read_text(encoding="utf-8")
            assert f"supersedes: [{r['superseded']}]" in text, r
            assert r["current"] != r["superseded"]
        # ---- the headroom assertions -------------------------------------
        # 🔴 The property W-95 exists to guarantee, and the ONE the previous
        # benchmark had no way to state: a contested query must have candidates
        # a bag-of-words ranker cannot separate. A power table says how many
        # queries; it never says whether the queries are HARD. These assertions
        # are where "hard" stops being a hope.
        rows = [
            json.loads(l)
            for l in (a / "eval" / "contested.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        assert rows, "no contested queries emitted"
        first_is_target = 0
        by_kind: dict[str, int] = {}
        for r in rows:
            terms = [
                t for t in r["q"].split()
                if t.startswith((CONTEST_PREFIX, HEADING_PREFIX, PATH_PREFIX))
            ]
            assert terms, r
            assert r["target"] in r["candidates"], r
            assert len(r["candidates"]) >= 2, r
            by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
            texts = {
                rel: (a / "repo" / rel).read_text(encoding="utf-8") for rel in r["candidates"]
            }

            if r["kind"] == "path":
                # The marker lives in the TARGET'S FILENAME and in NO prose;
                # in every distractor it lives in prose and in no filename.
                # Equal count, opposite field — that is the whole contest.
                for rel, text in texts.items():
                    in_path = terms[0] in rel
                    in_text = text.lower().split().count(terms[0])
                    if rel == r["target"]:
                        assert in_path and in_text == 0, f"{rel}: target must carry it in path only"
                    else:
                        assert not in_path and in_text == 1, f"{rel}: distractor must carry it in prose only"
            else:
                # Equal term frequency in EVERY candidate. A candidate carrying
                # the term more often would win on tf alone and the contest
                # would be decided before the ranker ran.
                for rel, text in texts.items():
                    for t in terms:
                        n_t = text.lower().split().count(t)
                        assert n_t == 1, f"{rel}: {t} tf == {n_t}, not 1"

            if r["kind"] == "proximity":
                x, y = terms
                same = [
                    rel for rel, text in texts.items()
                    if any(x in ln and y in ln for ln in text.splitlines())
                ]
                assert same == [r["target"]], (r["q"], same)
            elif r["kind"] == "heading":
                heads = [
                    rel for rel, text in texts.items()
                    if any(ln.startswith("## ") and terms[0] in ln for ln in text.splitlines())
                ]
                assert heads == [r["target"]], (r["q"], heads)

            first_is_target += int(r["candidates"][0] == r["target"])
        # The tie-break guard the chains carry, applied to clusters. If the
        # target were always the lexicographically first candidate, an engine
        # ordering ties by path would score 100 % and the number would be
        # measuring `sorted()`.
        assert 0 < first_is_target < len(rows), (
            f"target is path-first in {first_is_target}/{len(rows)} clusters — "
            "path order correlates with the answer"
        )
        print(
            "selftest ok: deterministic, no planted absent-entity, decoys silent, "
            f"chains linked, {len(rows)} contested clusters {by_kind} carry equal "
            "evidence and uncorrelated path order"
        )
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, help="environment directory")
    ap.add_argument("--docs", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0, help="same seed -> same bytes")
    ap.add_argument("--bench", action="store_true", help="plant chains, decoys, unanswerables")
    ap.add_argument("--pairs", type=int, default=240, help="bench: marker queries to emit")
    ap.add_argument("--chains", type=int, default=40, help="bench: supersession chains")
    ap.add_argument("--decoys", type=int, default=0, help="bench: decoy documents")
    ap.add_argument("--unanswerable", type=int, default=20, help="bench: decline probes")
    ap.add_argument("--contested", type=int, default=0, help="bench: proximity contests")
    ap.add_argument("--heading", type=int, default=0, help="bench: heading contests (control)")
    ap.add_argument("--path", type=int, default=0, help="bench: path contests")
    ap.add_argument("--cluster", type=int, default=4, help="bench: candidates per contest")
    ap.add_argument("--selftest", action="store_true", help="check the generator's own properties")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if args.out is None:
        ap.error("--out is required")

    if args.bench:
        decoys = args.decoys or max(1, args.docs // 20)
        report = generate_bench(
            args.out, args.docs, args.seed, args.pairs, args.chains, decoys,
            args.unanswerable, args.contested, args.heading, args.path, args.cluster
        )
        print(
            f"generated {report['docs']} docs · {report['pairs']} pairs · "
            f"{report['chains']} chains · {report['decoys']} decoys · "
            f"{report['unanswerable']} unanswerable · "
            f"{report['contested']} proximity · {report['heading']} heading · "
            f"{report['path']} path "
            f"(cluster {report['cluster']}) · seed {report['seed']}"
        )
        return 0

    report = generate(args.out, args.docs, args.seed)
    print(f"generated {report['docs']} docs, {report['pairs']} eval pairs, seed {report['seed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
