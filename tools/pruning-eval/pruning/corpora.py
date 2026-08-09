"""Corpus preparation and query sets.

Every corpus is ingested by the **archived v0.26 CLI as a black box**
(``python -m fux ingest`` in a subprocess, exactly as the archived eval harness
does) into a scratch working copy. Nothing under ``archive/`` is written to, and
the lab corpora are copied, never ingested in place.

Three corpora gate P1 — ``acme``, ``orbit``, ``synth`` — plus the tiny
``fixture`` corpus, which exists for developing the harness and is **not** a
gating corpus.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Corpus", "Query", "REPO", "ARCHIVE", "prepare", "load_files", "CORPORA"]

REPO = Path(__file__).resolve().parents[3]
ARCHIVE = REPO / "archive" / "v0.26"
LAB = Path.home() / "my_programs" / "fux-lab"


@dataclass(frozen=True)
class Query:
    """One eval query. ``gold`` is None when the gold label is baseline-derived."""

    text: str
    gold: str | None
    kind: str


@dataclass
class Corpus:
    name: str
    root: Path  # the ingested working copy
    queries: list[Query]
    gating: bool
    gold_source: str  # "committed-pairs" | "baseline-top1"
    note: str = ""


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ARCHIVE / "src")
    env.pop("VIRTUAL_ENV", None)
    # Determinism: the archived converters derive timestamps from this when set,
    # never from a wall clock (archived ADR-0002).
    env.setdefault("SOURCE_DATE_EPOCH", "0")
    return env


def _run_cli(cwd: Path, *args: str) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *args],
        cwd=cwd, env=_env(), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"fux {' '.join(args)} failed in {cwd}:\n{proc.stderr}")


def _copy_corpus(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src, dst,
        ignore=shutil.ignore_patterns(".fux", "fux.lock", ".git", "__pycache__", "_manifest.json"),
    )


def load_files(root: Path) -> dict[str, dict]:
    """The archived index's ``files`` dict, via whichever backend it landed in."""
    from fux.config import load as load_config
    from fux.index import backend_for

    config = load_config(root)
    return backend_for(config).load(root)


def load_params(root: Path):
    from fux.config import load as load_config

    return load_config(root).bm25f


# -- the corpora -----------------------------------------------------------


def _lab_pairs(env: str) -> list[Query]:
    """Committed Q→doc pairs from a fux-lab corpus manifest.

    ``unanswerable`` pairs carry no gold document and are excluded from every
    retrieval metric — declared in the pre-registration, not discovered here.
    """
    manifest = json.loads((LAB / env / "corpus" / "_manifest.json").read_text())
    return [
        Query(text=p["q"], gold=p["doc"], kind=p["kind"])
        for p in manifest["eval_pairs"]
        if p["kind"] != "unanswerable"
    ]


def _fixture_pairs() -> list[Query]:
    path = ARCHIVE / "tests_e2e" / "eval" / "pairs.jsonl"
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            pair = json.loads(line)
            out.append(Query(text=pair["q"], gold=pair["file"], kind="fixture"))
    return out


_WORD = re.compile(r"[a-z0-9_]+")
_SKIP = {"doc", "md", "see", "also", "citations", "tags", "title"}


def synth_queries(corpus_root: Path, docs: int, seed: int = 20260809) -> list[Query]:
    """A deterministic query set for the synthetic corpus.

    The synthetic corpus has **no human relevance judgments**, so its primary
    gold label is baseline-derived (see PRE-REGISTRATION §5.1). ``gold`` is left
    None here and filled from the baseline arm's top-1 at run time; the source
    document is carried in ``kind`` so the secondary known-item eval can use it.

    Three kinds, in fixed proportions: ``known-item`` (title terms, includes the
    document's index token and is therefore easy by construction), ``topical``
    (three body terms, index tokens excluded), ``phrase`` (a verbatim 5-token
    body span). Seeded; no wall clock, no unseeded randomness.
    """
    rng = random.Random(seed)
    plan = [("known-item", 50), ("topical", 75), ("phrase", 75)]
    total = sum(n for _, n in plan)
    step = max(1, docs // total)
    targets = [(i * step) % docs for i in range(total)]

    out: list[Query] = []
    cursor = 0
    for kind, count in plan:
        for _ in range(count):
            index = targets[cursor]
            cursor += 1
            rel = f"docs/doc-{index:06d}.md"
            text = (corpus_root / rel).read_text(encoding="utf-8")
            out.append(Query(text=_synth_query_text(kind, text, rng), gold=None,
                             kind=f"{kind}|{rel}"))
    return out


def _synth_query_text(kind: str, text: str, rng: random.Random) -> str:
    lines = text.splitlines()
    if kind == "known-item":
        for line in lines:
            if line.startswith("title: "):
                return line[len("title: "):].strip()
        return lines[0]
    body = [ln for ln in lines if ln and not ln.startswith(("#", "-", "title:", "tags:", "---"))]
    if kind == "phrase":
        line = body[rng.randrange(len(body))] if body else ""
        toks = _WORD.findall(line.lower())
        if len(toks) <= 5:
            return " ".join(toks)
        start = rng.randrange(len(toks) - 5)
        return " ".join(toks[start:start + 5])
    vocab = sorted({
        t for line in body for t in _WORD.findall(line.lower())
        if not t.isdigit() and t not in _SKIP and len(t) > 3
    })
    if not vocab:
        return ""
    picks = rng.sample(vocab, k=min(3, len(vocab)))
    return " ".join(picks)


def prepare(name: str, work: Path, *, synth_docs: int = 100_000, seed: int = 0) -> Corpus:
    """Build (or reuse) an ingested working copy and return its Corpus."""
    work.mkdir(parents=True, exist_ok=True)
    root = work / name

    if name == "fixture":
        if not (root / ".fux").exists():
            _copy_corpus(ARCHIVE / "tests_e2e" / "corpus", root)
            _run_cli(root, "setup", "-y", "--docs", "docs,notes,office",
                     "--code", "code", "--data", "data", "--images", "assets")
            _run_cli(root, "ingest")
        return Corpus(name, root, _fixture_pairs(), gating=False,
                      gold_source="committed-pairs",
                      note="9 documents — development corpus, not a gating corpus")

    if name in ("acme", "orbit"):
        src = LAB / name / "corpus"
        if not src.is_dir():
            raise SystemExit(
                f"{name} corpus not found at {src} — run ./setup.sh in {LAB / name}"
            )
        if not (root / ".fux").exists():
            _copy_corpus(src, root)
            _run_cli(root, "ingest")
        return Corpus(name, root, _lab_pairs(name), gating=True,
                      gold_source="committed-pairs",
                      note="realistic generated repo; committed human-authored pairs")

    if name == "synth":
        if not (root / ".fux").exists():
            if root.exists():
                shutil.rmtree(root)
            subprocess.run(
                [sys.executable, str(ARCHIVE / "tools" / "synth_corpus.py"),
                 "--docs", str(synth_docs), "--seed", str(seed), "--out", str(root)],
                env=_env(), check=True, capture_output=True, text=True,
            )
            _run_cli(root, "ingest")
        return Corpus(name, root, synth_queries(root, synth_docs), gating=True,
                      gold_source="baseline-top1",
                      note=f"{synth_docs} generated documents; no human relevance "
                           "judgments — gold is the baseline arm's top-1 (fidelity)")

    if name == "rfc":
        return _prepare_rfc(root)

    if name == "repodocs":
        return _prepare_repodocs(root)

    raise SystemExit(f"unknown corpus {name!r}")


# -- the long-document corpora (M1-rerun) ----------------------------------

RFC_LAB = LAB / "rfc"


def _prepare_rfc(root: Path) -> Corpus:
    """The RFC corpus — acquired once by `fetch_rfc.py`, verified by manifest.

    Nothing here touches the network: acquisition is a separate, explicit lab
    step, and this function fails loudly rather than silently fetching or
    silently substituting.
    """
    src = RFC_LAB / "corpus"
    manifest_path = RFC_LAB / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(
            f"no RFC corpus at {RFC_LAB} — acquire it first:\n"
            f"  archive/v0.26/.venv/bin/python tools/pruning-eval/fetch_rfc.py "
            f"--out {RFC_LAB}"
        )
    manifest = json.loads(manifest_path.read_text())
    if not (root / ".fux").exists():
        _copy_corpus(src, root)
        _run_cli(root, "setup", "-y", "--docs", "docs")
        _run_cli(root, "ingest")
    return Corpus("rfc", root, [], gating=True, gold_source="eval-set",
                  note=f"{len(manifest)} RFCs, manifest-pinned; long technical prose")


def verify_rfc_manifest(sample: int = 0) -> tuple[int, int]:
    """``(checked, mismatched)`` — the corpus is what the manifest says it is."""
    import hashlib

    manifest = json.loads((RFC_LAB / "manifest.json").read_text())
    keys = sorted(manifest)
    if sample:
        keys = keys[:: max(1, len(keys) // sample)]
    bad = 0
    for key in keys:
        path = RFC_LAB / "corpus" / "docs" / f"{key}.txt"
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest[key]:
            bad += 1
    return len(keys), bad


# The repo's own long-form documentation — the actual target domain. Small, but
# a disagreement between it and the RFCs is itself a finding (register and
# homogeneity differ in exactly the way that matters).
_REPODOC_ROOTS = (
    ("docs", "docs"),
    ("archive/v0.26/archive/v0.26-docs", "v026docs"),
    ("archive/v0.26/archive", "v026handoffs"),
    ("archive/v0.26/conformance", "v026conformance"),
    ("archive/v0.26/proposals", "v026proposals"),
    ("archive/v0.1/docs", "v01docs"),
)


def _prepare_repodocs(root: Path) -> Corpus:
    if not (root / ".fux").exists():
        if root.exists():
            shutil.rmtree(root)
        docs = root / "docs"
        docs.mkdir(parents=True)
        seen = 0
        for rel, prefix in _REPODOC_ROOTS:
            base = REPO / rel
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.md")):
                # Flatten, keeping provenance in the name so a gold label is
                # traceable back to the source document.
                flat = f"{prefix}__{path.relative_to(base).as_posix().replace('/', '__')}"
                target = docs / flat
                if target.exists():
                    continue
                target.write_bytes(path.read_bytes())
                seen += 1
        if not seen:
            raise SystemExit("no repo docs found — check _REPODOC_ROOTS")
        _run_cli(root, "setup", "-y", "--docs", "docs")
        _run_cli(root, "ingest")
    return Corpus("repodocs", root, [], gating=True, gold_source="eval-set",
                  note="the repo's own long-form docs — small, but the actual target domain")


CORPORA = ("fixture", "acme", "orbit", "synth", "rfc", "repodocs")
