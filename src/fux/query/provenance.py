"""How the returned output got generated — ADR-PROVENANCE.

Fux already tells a caller **what** it used (the citation, with a `sha`) and
**how much it believes it** ([ADR-CONFIDENCE](../../../docs/adr/0045_confidence.md)).
It has never told anyone **how it got there**, or **what it left out**. This
module is that third statement.

## The reframe: emit, don't retain

The word *audit trail* implies a log kept over time. Fux's answer to that is
the same one it gives the corpus: **it does not hold the trail, it makes one
derivable.** Every answer can be handed a **receipt** — a small,
content-addressed object naming the index it ranked against, the settings in
force, the engine that ran, and the bytes it cited — and `verify()` re-runs the
query against that receipt and reports whether the answer still reproduces.

That is the in-toto/SLSA shape (envelope → statement → predicate, subject named
by digest) rather than the logging shape, and it is the shape fux can actually
support: **fux is deterministic (L3), so a receipt is not a story about the
past, it is a re-runnable claim.**

⚠ **The four-state verdict is the load-bearing part, and it is not a boolean.**
This repo has now refused the same defect three times — `max_age_seconds`, a
`cached` verdict reported as `current`, and a line range for `ask` computed at
ingest. Each was a field that reported confidently on something it no longer
knew. A receipt is *by construction* a claim about a past moment, so
`verify()` must be able to say **"we did not look"** as loudly as it says
**"it matched"**:

| verdict | means |
|---|---|
| `reproduced` | the query was re-run and produced the same citation shas |
| `drifted:corpus` | the index moved — the receipt names which digest changed |
| `drifted:config` | the tune file or the engine version differs |
| `unverifiable` | the index root is gone, or a `url:` source cannot be reached |

Folding `unverifiable` into `drifted` would be the fourth instance of the
defect, and folding it into `reproduced` would be the first *dangerous* one.

## L8, and why this module may write plaintext

L8 was written on the morning of 2026-08-27 and **reverted by Arpit the same
day**: a use record may now carry the question and the answer in plaintext,
because a log nobody can read answers no question anyone asks of it. What
survives is confinement — the journal lives in `.fux/runtime/`, which
[`store/fuxdir.py`](../store/fuxdir.py) lists by name as gitignored, and it
**never reaches a committed byte or the network**. See
[ADR-LAWS](../../../docs/adr/0001_laws.md) decision 8, which also records that
the AOL-2006 risk was *accepted*, not disproved.

⚠ **The journal is OFF by default.** Turning plaintext logging on for every
existing consumer without asking is exactly the surprise a `$0`, offline,
"nothing leaves your machine" tool must not spring. `[provenance] journal =
true` in `.fux/tune.toml` opts in; `journal_max` bounds it. The bound is a
*design default*, not a law — L8 no longer requires one, and Arpit's standing
rule is to state the cost rather than clamp the knob.

## What the derivation may claim, and what it may not

**Everything here is recomputed from what ranking already produced.** The
scorer is not instrumented, no per-term contribution is threaded through the
hot path, and no candidate path changed. That is deliberate and it is Lucene's
own discipline: `explain` is a *second query against one document*, never a tax
on the first. Concretely, a derivation reads:

- the committed record's `terms` map (per-field counts, already on disk),
- the `df`/`n` corpus statistics `stats_out` already hands back for
  [ADR-CONFIDENCE](../../../docs/adr/0045_confidence.md),
- the ordering the caller was actually shown.

⚠ **It therefore reports *observed* quantities, never a reconstructed score.**
`rank.py`'s own docstring warns that re-deriving a score term-by-term produces
different low-order bits than the sum that produced it. A derivation that
printed a recomputed total would be a plausible number that disagreed with the
one beside it, which is worse than no number. So the score is quoted from the
result, and the attribution explains *which terms and fields were available to
it* — a claim that is exactly true.

## The four gates

The funnel is [ADR-QUALITY](../../../docs/adr/0044_quality-contract.md)'s, not
a new invention: `reachable` → `in window` → `placed` → `answered`. Attributing
a miss to a gate is the whole reason the contract chose a funnel over a blended
score, and it is the audit-valuable half of a derivation — *what was left out,
and where it fell out* — which no citation list can show.

Reference: Elastic, *Elasticsearch scoring and the Explain API* —
https://www.elastic.co/search-labs/blog/elasticsearch-scoring-and-explain-api
· SLSA v1.0, *Software attestations* — https://slsa.dev/spec/v1.0/attestation-model
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from ..store import fuxdir

#: The declared shape. Bumped only when a key changes meaning — a consumer
#: that stored receipts under v1 must be able to tell.
#: The in-toto Statement type. Ruled by Arpit 2026-08-27: **adopt the standard
#: shape, sign nothing.**
#:
#: A Statement is `_type` · `subject` · `predicateType` · `predicate`, and it is
#: **valid on its own** — the DSSE envelope that carries a signature is a
#: separate layer. So fux emits a payload the ecosystem already knows how to
#: read, and a consumer who needs a signature wraps it with `cosign` **using
#: their own identity**, which is the only way it means anything.
#:
#: ⚠ **stdlib `hmac` was considered and REFUSED**, and not merely as "weaker":
#: HMAC provides integrity and authenticity but **NOT non-repudiation**, because
#: verifying needs the same secret that signs. With a repo-shared key every
#: developer and the CI runner can produce any receipt and each can deny
#: producing one — so a signature would imply accountability it structurally
#: cannot carry.
#:
#: ⚠ **Keyless signing is the right answer and fux cannot have it.** Sigstore
#: shifts the trust anchor from key management to identity management, and needs
#: a network (L4), an OIDC identity, a transparency-log service (`$0`) and
#: non-stdlib dependencies (L1) — four constraints at once.
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"

#: What kind of claim the `predicate` carries. A TypeURI, versioned separately
#: from the Statement schema so fux's payload can change without pretending the
#: envelope did.
PREDICATE_TYPE = "https://fux.dev/receipt/v1"

#: ⚠ **Retained ONLY to reject a v1 receipt with a useful message.** Nothing
#: writes it. A `fux.receipt.v1` payload predates the in-toto reshape and cannot
#: be verified against the current shape, and *"not a fux receipt"* would send a
#: reader hunting for corruption in a file that is merely old.
LEGACY_SCHEMA = "fux.receipt.v1"

JOURNAL_NAME = "provenance.jsonl"

#: Bound on journalled receipts. A *design* default, not a law: L8 as reverted
#: requires confinement, not a size. The oldest entries are dropped, because
#: the value of a use record is overwhelmingly in the recent tail.
DEFAULT_JOURNAL_MAX = 1000

#: `verify()`'s four states. Never collapse these into a boolean.
REPRODUCED = "reproduced"
DRIFTED_CORPUS = "drifted:corpus"
DRIFTED_CONFIG = "drifted:config"
UNVERIFIABLE = "unverifiable"

VERDICTS = (REPRODUCED, DRIFTED_CORPUS, DRIFTED_CONFIG, UNVERIFIABLE)


# -- identity ------------------------------------------------------------------


def index_digest(root: Path) -> str:
    """A reproducible digest of the committed index, or `""` when there is none.

    **The committed shards, not the runtime stamp.**
    [ADR-RUNTIME-STAMP](../../../docs/adr/0027_runtime-stamp.md) decision 2
    deliberately excludes the stamp from `DETERMINISTIC_FILES` because mtimes
    differ between two checkouts of byte-identical content. A receipt keyed on
    the stamp would therefore fail to reproduce on a fresh clone **by
    construction** — the trap that record already warns about, arriving one
    plane later.

    Shard paths are sorted by `iter_shard_paths`, so this is stable across
    filesystems and is the same on every machine holding the same commit.
    """
    from .. import store as store_mod

    try:
        paths = store_mod.iter_shard_paths(root)
    except Exception:
        return ""
    if not paths:
        return ""
    digest = hashlib.sha256()
    for path in paths:
        try:
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        except OSError:
            return ""
    return digest.hexdigest()


def tune_digest(root: Path) -> str:
    """`sha256` of `.fux/tune.toml`, or `"none"` when the file is absent.

    `"none"` and a digest are different states and must stay so: an answer that
    changed because somebody *added* a tune file has drifted on config exactly
    as much as one whose weights were edited.
    """
    path = fuxdir.fux_dir(root) / "tune.toml"
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "none"


# -- the derivation ------------------------------------------------------------


@dataclass(frozen=True)
class TermHit:
    """One query term, as the document actually carries it.

    `fields` is the committed per-field count array — the record's own numbers,
    not a reconstruction. `df` is the corpus document frequency the ranking
    pass already computed.
    """

    term: str
    analyzed: str
    df: int
    fields: tuple[int, ...] = ()
    #: W-109 — `True` when this term came from `--expand` rather than from the
    #: question. **`--why` exists to answer *why is this document here*, and
    #: *"because the caller supplied the word"* is a different answer from
    #: *"because you asked for it"***. Present on every hit, never only on the
    #: expanded ones, so a consumer reads a value rather than an absence.
    expanded: bool = False

    def as_dict(self) -> dict:
        return {
            "term": self.term,
            "analyzed": self.analyzed,
            "df": self.df,
            "fields": list(self.fields),
            "expanded": self.expanded,
        }


@dataclass(frozen=True)
class DocDerivation:
    """Why one returned document is where it is."""

    id: str
    loc: str
    score: float
    rank: int
    matched: tuple[TermHit, ...] = ()
    missing: tuple[str, ...] = ()
    archived: bool = False
    multiplier: float = 1.0
    rank_before_rerank: int | None = None
    rank_untuned: int | None = None

    def as_dict(self) -> dict:
        out = {
            "id": self.id,
            "loc": self.loc,
            "score": self.score,
            "rank": self.rank,
            "matched": [t.as_dict() for t in self.matched],
            "missing": list(self.missing),
            "archived": self.archived,
            "multiplier": self.multiplier,
        }
        # Additive and honest: absent means *not computed on this run*, which
        # is a different statement from "unchanged". Present-but-equal is the
        # way to say unchanged.
        if self.rank_before_rerank is not None:
            out["rank_before_rerank"] = self.rank_before_rerank
        if self.rank_untuned is not None:
            out["rank_untuned"] = self.rank_untuned
        return out


@dataclass(frozen=True)
class Gates:
    """ADR-QUALITY's funnel, as counts. The negative space, in four integers."""

    reachable: int
    in_window: int
    placed: int
    answered: int
    cut_score: float | None = None

    def as_dict(self) -> dict:
        return {
            "reachable": self.reachable,
            "in_window": self.in_window,
            "placed": self.placed,
            "answered": self.answered,
            "cut_score": self.cut_score,
        }


@dataclass
class Derivation:
    """The whole `--why` block."""

    query: str
    path: str
    gates: Gates
    documents: list[DocDerivation] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "query": self.query,
            "path": self.path,
            "gates": self.gates.as_dict(),
            "documents": [d.as_dict() for d in self.documents],
        }


def _record_terms(record: dict | None) -> dict:
    if not isinstance(record, dict):
        return {}
    terms = record.get("terms")
    return terms if isinstance(terms, dict) else {}


def derive(
    root: Path,
    query: str,
    results,
    *,
    path: str,
    stats: dict | None = None,
    records=None,
    window=None,
    pre_rerank=None,
    untuned=None,
    multiplier: float = 1.0,
    expand: str = "",
) -> Derivation:
    """Build the derivation for a result list. **Never raises.**

    `records` is a callable `doc_id -> record | None`, injected rather than
    imported so this module never reaches into the store's read path on its
    own — the same seam `refer/` uses for fetchers, and for the same reason.

    `window` is the pre-truncation candidate list (what `depth` retrieved), and
    is what makes the `in window` gate and the cut line real rather than a
    restatement of `placed`.
    """
    from .analyzer import analyze_pairs
    from .scan import query_term_hashes

    stats = stats or {}
    df_map = stats.get("df") or {}
    n = int(stats.get("n", 0) or 0)

    try:
        pairs = list(analyze_pairs(query))
    except Exception:
        pairs = []
    try:
        hashes = list(query_term_hashes(query))
    except Exception:
        hashes = []
    # ⚠ **`query_term_hashes` DEDUPES on the hash and `analyze_pairs` does
    # not**, so `zip` would silently misalign every term after a repeated word
    # — the exact trap [`confidence.py`](confidence.py) names. Key by hash and
    # keep the first surface, which is what that module does and what makes the
    # two blocks agree by construction rather than by review.
    from .. import store as store_mod

    first: dict[str, str] = {}
    analyzed_of: dict[str, str] = {}
    for surface, analyzed in pairs:
        h = store_mod.term_hash(analyzed)
        first.setdefault(h, surface)
        analyzed_of.setdefault(h, analyzed)
    # W-109 — the expansion's own terms, appended so `--why` can say *"this
    # document is here because the CALLER supplied the word"*, which is a
    # different answer from *"because you asked for it"*.
    #
    # ⚠ **Appended to `matched`, deliberately NOT to `missing`.** `missing` is
    # a claim about the user's question — it is what `ask` prints and what the
    # retry rule reads — and filling it with words a model guessed and the
    # document happens to lack would turn a signal into noise.
    supplied: set[str] = set()
    extra: list[tuple[tuple[str, str], str]] = []
    if expand:
        try:
            seen = set(hashes)
            for surface, analyzed in analyze_pairs(expand):
                h = store_mod.term_hash(analyzed)
                if h in seen:
                    continue
                seen.add(h)
                supplied.add(h)
                extra.append(((surface, analyzed), h))
        except Exception:
            supplied, extra = set(), []

    aligned = [((first.get(h, h), analyzed_of.get(h, "")), h) for h in hashes]

    before = {r.id: i for i, r in enumerate(pre_rerank or [])}
    untuned_rank = {r.id: i for i, r in enumerate(untuned or [])}

    docs: list[DocDerivation] = []
    for position, result in enumerate(results):
        record = None
        if records is not None:
            try:
                record = records(result.id)
            except Exception:
                record = None
        carried = _record_terms(record)
        hits: list[TermHit] = []
        absent: list[str] = []
        for (surface, analyzed), term_hash in [*aligned, *extra]:
            counts = carried.get(term_hash)
            if counts is None:
                # An expansion term the document lacks is not "missing" — see
                # the note above. It simply did not fire.
                if term_hash not in supplied:
                    absent.append(surface)
                continue
            hits.append(
                TermHit(
                    term=surface,
                    analyzed=analyzed,
                    df=int(df_map.get(term_hash, 0) or 0),
                    fields=tuple(int(c) for c in counts) if isinstance(counts, list) else (),
                    expanded=term_hash in supplied,
                )
            )
        docs.append(
            DocDerivation(
                id=result.id,
                loc=result.loc,
                score=float(result.score),
                rank=position,
                matched=tuple(hits),
                missing=tuple(absent),
                archived=bool(getattr(result, "archived", False)),
                multiplier=multiplier if getattr(result, "archived", False) else 1.0,
                rank_before_rerank=before.get(result.id),
                rank_untuned=untuned_rank.get(result.id),
            )
        )

    candidates = list(window) if window is not None else list(results)
    cut = float(candidates[-1].score) if candidates else None
    gates = Gates(
        reachable=n,
        in_window=len(candidates),
        placed=len(list(results)),
        answered=1 if results else 0,
        cut_score=cut,
    )
    return Derivation(query=query, path=path, gates=gates, documents=docs)


# -- the receipt ---------------------------------------------------------------


def receipt(
    root: Path,
    query: str,
    *,
    path: str,
    subject,
    confidence: dict | None = None,
    derivation: Derivation | None = None,
    verdicts=None,
    expand: str = "",
) -> dict:
    """A content-addressed record of one answer.

    `subject` is the list the answer actually cited — `{id, loc, sha}` each,
    named by digest, which is what makes the receipt checkable rather than
    merely descriptive (SLSA's *subject*).

    `expand` is W-109's agent-written expansion, recorded **verbatim**. It is
    an input to the ranking exactly as `query` is, so a receipt that omitted it
    would describe an answer nobody could reproduce — the caller would re-run
    the bare question and get a different list. ⚠ **Absent means no expansion
    was passed**, never "unknown": the key is written only when there was one,
    the same additive rule every other optional key here follows (W-48).

    ⚠ **L8, and the reason this is legal.** An expansion is a *use record* —
    what someone asked and how — so it lives on the receipt and the journal,
    both gitignored, and reaches no committed byte.

    ⚠ **No wall clock.** L3 forbids one on a deterministic path and, more
    practically, a timestamp would make two receipts for the same answer
    differ, which defeats the whole point of a re-runnable claim. The caller
    who wants a time stamps it on the outside — the same rule the runtime
    manifest follows.
    """
    from .. import __version__

    return {
        "_type": STATEMENT_TYPE,
        "subject": [_resource(s) for s in (subject or [])],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "engine": {"version": __version__, "path": path},
            "inputs": {
                "index": index_digest(root),
                "tune": tune_digest(root),
                "query": query,
                **({"expand": expand} if expand else {}),
            },
            "confidence": dict(confidence) if confidence else {},
            "derivation": derivation.as_dict() if derivation is not None else {},
            "verdicts": [dict(v) for v in (verdicts or [])],
        },
    }


def _resource(cited: dict) -> dict:
    """One cited document as an in-toto **ResourceDescriptor**.

    `{id, loc, sha}` maps almost exactly: `id` -> `name`, `sha` ->
    `digest.sha256`. **The mapping is a rename, not a reshape** — fux already
    cited by digest, which is the whole reason the standard shape fits.

    ⚠ **`loc` has no field in a ResourceDescriptor.** A line range is not a URI
    and not a digest, so it goes in `annotations`, which is the spec's own
    extension point — namespaced, because an unnamespaced key in a shared
    schema is how two tools collide.
    """
    sha = str(cited.get("sha", ""))
    resource = {"name": str(cited.get("id", "")), "digest": {"sha256": sha}}
    loc = cited.get("loc")
    if loc:
        resource["annotations"] = {"fux.dev/loc": str(loc)}
    return resource


def receipt_sha(payload: dict) -> str:
    """The digest a caller quotes instead of carrying the whole receipt.

    Canonical JSON — sorted keys, no incidental whitespace — so the same
    receipt hashes the same on every machine.
    """
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# -- the journal ---------------------------------------------------------------


def journal_path(root: Path) -> Path:
    return fuxdir.fux_dir(root) / "runtime" / JOURNAL_NAME


def remember(root: Path, payload: dict, *, max_entries: int = DEFAULT_JOURNAL_MAX) -> None:
    """Append a receipt to the local journal. **Never raises.**

    Gitignored, local, never transmitted — the whole of what L8 still requires.
    Rewrites the file when the bound is exceeded rather than appending forever;
    at the default that is a few hundred kilobytes and one rewrite per thousand
    answers, which is cheaper than any rotation scheme worth its complexity.
    """
    if max_entries <= 0:
        return
    try:
        fuxdir.derived_dir(root, "runtime")
        path = journal_path(root)
        line = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        existing: list[str] = []
        if path.exists():
            existing = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        existing.append(line)
        if len(existing) > max_entries:
            existing = existing[-max_entries:]
        path.write_text("\n".join(existing) + "\n", encoding="utf-8")
    except Exception:  # pragma: no cover - a use record must not break an answer
        pass


def read_journal(root: Path) -> list[dict]:
    """Every receipt on disk, oldest first. `[]` on any failure."""
    try:
        text = journal_path(root).read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


# -- verification --------------------------------------------------------------


@dataclass(frozen=True)
class Verification:
    """`verify()`'s answer. `verdict` is one of `VERDICTS` and never a bool."""

    verdict: str
    note: str = ""
    expected: tuple[str, ...] = ()
    actual: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "note": self.note,
            "expected": list(self.expected),
            "actual": list(self.actual),
        }


def _sha_of(entry) -> str:
    """The sha of one cited document, from either shape.

    A receipt's `subject` holds in-toto ResourceDescriptors
    (`digest.sha256`); `verify`'s `rerun` callback hands back fux's internal
    `{id, sha}`. **Both are read here rather than at two call sites**, because
    a missing key would degrade to `""` and two empty strings compare EQUAL —
    which would report `reproduced` for a receipt that verified nothing.
    """
    if not isinstance(entry, dict):
        return ""
    digest = entry.get("digest")
    if isinstance(digest, dict) and digest.get("sha256"):
        return str(digest["sha256"])
    return str(entry.get("sha", ""))


def verify(root: Path, payload: dict, *, rerun=None) -> Verification:
    """Check a receipt against this working tree.

    **Config is checked before corpus, and both before the re-run.** A tune
    edit changes the answer without changing a single indexed byte, so
    reporting `drifted:corpus` for it would name the wrong cause — and naming
    the wrong cause is how an audit trail becomes worse than none.

    `rerun` is an optional callable `(query) -> [{"id","sha"}...]` that
    re-answers the question. Without it, this verifies the *inputs* only and
    says so in `note` rather than claiming a reproduction it did not perform —
    "we did not look" stays visible.
    """
    if not isinstance(payload, dict):
        return Verification(UNVERIFIABLE, note="not a fux receipt")
    if payload.get("schema") == LEGACY_SCHEMA:
        # ⚠ Named, not lumped in with corruption. A v1 receipt predates the
        # in-toto reshape; telling its holder it is "not a fux receipt" sends
        # them looking for damage in a file that is simply old.
        return Verification(
            UNVERIFIABLE,
            note=f"{LEGACY_SCHEMA} predates the in-toto shape and cannot be verified here",
        )
    if payload.get("_type") != STATEMENT_TYPE:
        return Verification(UNVERIFIABLE, note="not a fux receipt")
    if payload.get("predicateType") != PREDICATE_TYPE:
        # A well-formed in-toto Statement carrying somebody else's predicate.
        # Precise, because this one IS a valid attestation — just not ours.
        return Verification(
            UNVERIFIABLE,
            note=f"in-toto Statement, but predicateType is {payload.get('predicateType')!r}",
        )

    predicate = payload.get("predicate") or {}
    inputs = predicate.get("inputs") or {}
    engine = predicate.get("engine") or {}

    from .. import __version__

    if engine.get("version") != __version__:
        return Verification(
            DRIFTED_CONFIG,
            note=f"engine {engine.get('version')} -> {__version__}",
        )

    now_tune = tune_digest(root)
    if inputs.get("tune") != now_tune:
        return Verification(DRIFTED_CONFIG, note="tune.toml differs")

    now_index = index_digest(root)
    if not now_index:
        return Verification(UNVERIFIABLE, note="no committed index in this tree")
    if inputs.get("index") != now_index:
        return Verification(DRIFTED_CORPUS, note="the committed index differs")

    expected = tuple(_sha_of(s) for s in payload.get("subject") or [])
    if rerun is None:
        return Verification(
            UNVERIFIABLE,
            note="inputs match; the answer was not re-run",
            expected=expected,
        )
    try:
        again = rerun(inputs.get("query", ""))
    except Exception as exc:  # pragma: no cover - defensive
        return Verification(UNVERIFIABLE, note=f"re-run failed: {exc}", expected=expected)

    # ⚠ `rerun` hands back fux's own `{id, sha}`, NOT ResourceDescriptors — it
    # is an internal callback, not a receipt. `_sha_of` reads both shapes so the
    # comparison cannot silently compare a digest against an empty string.
    actual = tuple(_sha_of(s) for s in again or [])
    if actual == expected:
        return Verification(REPRODUCED, expected=expected, actual=actual)
    return Verification(
        DRIFTED_CORPUS,
        note="the cited bytes differ",
        expected=expected,
        actual=actual,
    )
