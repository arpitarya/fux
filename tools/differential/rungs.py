"""Resolve a golden-ladder rung to a corpus root, and verify it against the
committed manifest before anything measures it.

W-107. [PRE-REG-NODE-2](../../work/benchmark/PRE-REGISTRATION-NODE-2.md) §4
fixes the corpora for the Node differential arm: the committed golden ladder,
rungs 100 through 10 000, in **fux-lab and nowhere else**
([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)).

**The rung is not in this repo; its manifest is.** `work/golden/ladder/` holds
`rung-NNNNN.sha256` (every document, by hash) and `rung-NNNNN.index` (the
engine version and the index root hash the rung was built with); the corpus
itself lives at `~/my_programs/fux-lab/corpora/golden/<rung>/`
([`work/golden/README.md`](../../work/golden/README.md)). This module is the
join between the two, and it exists because *"the arm ran on rung-10000"* is a
claim about a corpus nobody reading the evidence can see.

🔴 **Verification is not a formality, it is the whole reason the manifests are
committed.** An arm that runs on a drifted rung produces a number that names a
corpus it did not measure — and a Node/Python comparison is exactly the shape
of run where that failure is invisible, because *both* readers would see the
same drifted bytes and agree perfectly.

🔴 **Never reads `work/golden/questions/` or any path holding an answer.**
The arm compares two readers against each other and needs no ground truth
(PRE-REG-NODE-2 §4); the manifests name `seed/` and `ext/` documents only, and
the one directory this module opens under `work/golden/` is `seed/`, which
[L11](../../records/0012_LAW-11-sealed-answer-key.md) permits — `seed_drift()`
needs the live bytes to know a rung has gone stale.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

#: This repository — where the committed manifests live. Not the corpus.
REPO = Path(__file__).resolve().parents[2]
LADDER = REPO / "work" / "golden" / "ladder"

#: The live seed corpus every rung copies. The ONE directory under
#: `work/golden/` this module may read (L11); `questions/` is never touched.
SEED = REPO / "work" / "golden" / "seed"

#: Where the ladder corpus lives. `FUX_GOLDEN_CORPORA` overrides it, which is
#: what lets a second lab checkout run the arm without editing this file.
DEFAULT_CORPORA = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"

#: The two rungs PRE-REG-NODE-2 §4 names for every push: the ends of the
#: ladder. The six between them differ in size, not in kind.
ENDS = ("rung-00100", "rung-10000")


class RungError(RuntimeError):
    """A rung is missing, drifted, or not a rung. Always fatal to a run."""


def corpora_root() -> Path:
    return Path(os.environ.get("FUX_GOLDEN_CORPORA") or DEFAULT_CORPORA)


def rung_names() -> list[str]:
    """Every rung the committed ladder declares, smallest first.

    Derived from the manifests, never from the corpus directory — the ladder is
    what this repo froze, and a stray directory in the lab is not a rung.
    """
    return sorted(p.stem for p in LADDER.glob("rung-*.index"))


def manifest(name: str) -> dict[str, str]:
    """`rung-NNNNN.index` as a dict — engine, rung, documents, root sha, commit."""
    path = LADDER / f"{name}.index"
    if not path.exists():
        raise RungError(f"no such rung in the committed ladder: {name!r} ({path})")
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


def documents(name: str) -> list[tuple[str, str]]:
    """`(sha256, relative path)` for every document in the rung, in manifest order."""
    path = LADDER / f"{name}.sha256"
    if not path.exists():
        raise RungError(f"no document manifest for {name!r} ({path})")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 2:
            raise RungError(f"{path}: unparseable manifest line {line!r}")
        rows.append((parts[0], parts[1]))
    return rows


def seed_documents() -> dict[str, str]:
    """`{path: sha256}` for the LIVE `work/golden/seed/`, keyed as a rung holds it.

    Paths are `seed/<name>` because that is how `build_golden_rung.py` copies
    them into a rung and how the manifests name them.
    """
    out: dict[str, str] = {}
    for path in sorted(SEED.rglob("*")):
        if path.is_file():
            rel = "seed/" + path.relative_to(SEED).as_posix()
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def seed_drift(name: str) -> list[str]:
    """Every way rung `name`'s manifest disagrees with the live seed. Empty = clean.

    🔴 **This is the check nothing had, and its absence cost the ladder twice.**
    `verify()` compares a rung against its manifest and `ladder_check` compares
    the manifests against each other — so on 2026-09-15, when seven of the
    twenty seed documents grew by 131 lines in this repo, all eight rungs went
    on agreeing with themselves perfectly while carrying the OLD text. A rung
    whose seed has moved answers questions written against words it does not
    contain, and the number that comes back is indistinguishable from a real
    one.

    The `ext/` half is deliberately NOT checked here: it lives only in the lab
    and is reproducible from the committed generator, which is `verify()`'s job.
    """
    live = seed_documents()
    frozen = {rel: sha for sha, rel in documents(name) if rel.startswith("seed/")}

    problems: list[str] = []
    missing = sorted(set(live) - set(frozen))
    extra = sorted(set(frozen) - set(live))
    drifted = sorted(rel for rel in set(live) & set(frozen) if live[rel] != frozen[rel])
    if missing:
        problems.append(
            f"{name}: {len(missing)} seed document(s) absent from the manifest: {missing[:3]}"
        )
    if extra:
        problems.append(
            f"{name}: {len(extra)} manifest seed path(s) no longer in work/golden/seed/: {extra[:3]}"
        )
    if drifted:
        problems.append(
            f"{name}: {len(drifted)} seed document(s) changed since the rung was frozen "
            f"— rebuild it (prompt 4) or the rung answers against stale text: {drifted[:3]}"
        )
    return problems


def index_root_sha256(root: Path) -> str:
    """The rung's index root hash, computed the way the builder computed it.

    Path bytes then file bytes, over `sorted(rglob("*"))` — `build_golden_rung.py`
    §"the three ladder records". Restated here only as executable code, which is
    the one form [L0](../../records/0002_LAW-0-authority.md) permits: it cannot
    disagree with the manifest and still look correct, it simply fails.
    """
    digest = hashlib.sha256()
    for path in sorted((root / ".fux" / "index").rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def verify(name: str, root: Path, *, documents_too: bool = True) -> list[str]:
    """Every way this corpus disagrees with the committed manifest. Empty = clean.

    The index root hash is always checked — it is the cheap one and it is what
    the arm actually reads. `documents_too=False` skips the per-document pass,
    which is 10 000 file hashes on the top rung.
    """
    problems: list[str] = []
    meta = manifest(name)

    if not (root / ".fux" / "index").is_dir():
        return [f"{root}: no .fux/index — not an ingested rung"]

    actual = index_root_sha256(root)
    if actual != meta.get("index_root_sha256"):
        problems.append(
            f"index root sha256: manifest={meta.get('index_root_sha256')} corpus={actual} "
            f"— the rung was rebuilt or the index edited; re-freeze it or run an older engine"
        )

    declared = documents(name)
    if documents_too:
        missing, drifted = 0, 0
        first: list[str] = []
        for want, rel in declared:
            path = root / rel
            if not path.exists():
                missing += 1
                if len(first) < 3:
                    first.append(f"missing: {rel}")
                continue
            got = hashlib.sha256(path.read_bytes()).hexdigest()
            if got != want:
                drifted += 1
                if len(first) < 3:
                    first.append(f"drifted: {rel} (manifest={want[:12]}… corpus={got[:12]}…)")
        if missing or drifted:
            problems.append(
                f"documents: {missing} missing, {drifted} drifted of {len(declared)}"
            )
            problems.extend(f"  {row}" for row in first)

    count = meta.get("documents")
    if count and count.isdigit() and int(count) != len(declared):
        problems.append(
            f"manifest disagrees with itself: .index says {count} documents, "
            f".sha256 lists {len(declared)}"
        )
    return problems


def resolve(name: str, *, verify_documents: bool = True) -> Path:
    """The corpus root for a rung, verified. Raises rather than measuring drift."""
    if name not in rung_names():
        raise RungError(
            f"{name!r} is not a rung in the committed ladder. "
            f"Known: {', '.join(rung_names()) or '(none)'}"
        )
    root = corpora_root() / name
    if not root.is_dir():
        raise RungError(
            f"the ladder corpus is not on this machine: {root} does not exist.\n"
            f"  The rungs live in fux-lab (SR-WORK-ENVIRONMENTS), are not committed (work/golden/README.md),\n"
            f"  and are rebuilt with build_golden_rung.py. Set FUX_GOLDEN_CORPORA to\n"
            f"  point at another checkout."
        )
    problems = verify(name, root, documents_too=verify_documents)
    if problems:
        raise RungError(
            f"{name} at {root} does not match the committed manifest:\n  "
            + "\n  ".join(problems)
        )
    return root
