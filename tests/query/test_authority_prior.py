"""W-168 step 8 — the git authority prior: the counts, the prior, both readers.

What the frozen bar requires of the build
([PRE-REGISTRATION](../../work/regression/2026-09-28-authority-prior/PRE-REGISTRATION.md)
§The mechanism), one test per row:

- ingest's ONE walk writes `authors` (distinct case-folded `%aE`) and `commits`
  (commits listing the path; a merge counts 0) on each git-sourced record;
- no history — no repository, a shallow clone — writes neither;
- no name, email or hash of either reaches a committed byte;
- `authority_weight = 0.0` never reads the counts and is the engine before the
  key, byte for byte;
- on, the score is multiplied by exactly `1 + w * (1 - 1/(authors * commits))`;
- the accelerator's supremum carries `1 + w`, and scan = accelerator at every
  arm value, with `[priority]` and the intent prior stacked;
- `fux lexical` never applies it;
- `--why` names it on a document it moved, and only then;
- the Node reader ranks identically.
"""

from __future__ import annotations

from l12_fixtures import scoring, template_tune, tune_text, tuned, write_config
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fux import store as store_mod
from fux.derive import build
from fux.ingest.run import run
from fux.query import rank as rank_mod
from fux.query import run_query
from fux.query.rank import Weighting
from fux.query.scan import ask as scan_ask

ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"

#: Who touched what. Two spellings of one mailbox are ONE author: the walk
#: case-folds `%aE`, which is the A3 ruling's "distinct authors".
HISTORY = (
    ("docs/maintained-cold-chain.md", "alice@example.org"),
    ("docs/maintained-cold-chain.md", "bob@example.org"),
    ("docs/maintained-cold-chain.md", "BOB@Example.org"),
    ("docs/maintained-cold-chain.md", "carol@example.org"),
    ("docs/pair-cold-chain.md", "alice@example.org"),
    ("docs/pair-cold-chain.md", "alice@example.org"),
    ("docs/draft-cold-chain.md", "dave@example.org"),
)
EXPECTED = {
    "docs/maintained-cold-chain.md": (3, 4),
    "docs/pair-cold-chain.md": (1, 2),
    "docs/draft-cold-chain.md": (1, 1),
    "docs/branch-cold-chain.md": (1, 1),  # the merge commit that brought it in counts 0
}
QUESTIONS = ("cold chain", "cold chain revision", "filler body text", "reefer seal")
PRIORITY = (("docs/draft", 2.0), ("docs/p", 0.5))
DOCTYPE = (("*-procedure-*", "procedure"),)


def _git(root: Path, *argv: str, email: str = "setup@example.org") -> None:
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="Someone",
        GIT_AUTHOR_EMAIL=email,
        GIT_COMMITTER_NAME="Someone",
        GIT_COMMITTER_EMAIL=email,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
    )
    try:
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *argv],
            cwd=root, env=env, check=True, capture_output=True, text=True,
        )
    except OSError:  # pragma: no cover - git is a dev prerequisite
        pytest.skip("git unavailable")


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _history(root: Path) -> Path:
    """A repository whose documents carry the counts in `EXPECTED`."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    for i in range(6):
        _write(root, f"docs/filler-{i:02d}.md", f"# Filler {i}\n\nfiller body text number {i}\n")
    _write(root, "docs/40-procedure-reefer.md", "# Reefer seal\n\nHow to seal a reefer for the cold chain.\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fillers", email="setup@example.org")
    for n, (rel, email) in enumerate(HISTORY):
        _write(root, rel, f"# Cold chain {rel}\n\nThe cold chain rule, revision {n}.\n")
        _git(root, "add", rel)
        _git(root, "commit", "-q", "-m", f"edit {n}", email=email)
    _git(root, "checkout", "-q", "-b", "side")
    _write(root, "docs/branch-cold-chain.md", "# Branch\n\nA cold chain note from a branch.\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "side", email="erin@example.org")
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "-m", "merge side", "side", email="frank@example.org")
    return root


def _configure(root: Path, tune: str | None = None) -> Path:
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    if tune is not None:
        (root / ".fux" / "tune.toml").write_text(tune, encoding="utf-8")
    write_config(root)
    return root


def _ingest(root: Path, *, full: bool = False) -> Path:
    run(root, refresh_urls=False, full=full)
    build(root)
    return root


def _corpus(root: Path, tune: str | None = None) -> Path:
    return _ingest(_configure(_history(root), tune))


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    return _corpus(tmp_path_factory.mktemp("authority"))


def _records(root: Path) -> dict[str, dict]:
    return {r["loc"]: r for r in store_mod.read_index(root).values()}


def _payload(results):
    return [(r.id, round(r.score, 9)) for r in results]


# -- the counts ----------------------------------------------------------------


def test_the_walk_writes_distinct_authors_and_commits(corpus):
    records = _records(corpus)
    for loc, (authors, commits) in EXPECTED.items():
        assert (records[loc]["authors"], records[loc]["commits"]) == (authors, commits), loc
    assert (records["docs/filler-00.md"]["authors"], records["docs/filler-00.md"]["commits"]) == (1, 1)
    assert all("mtime" in r for r in records.values()), "the walk still writes mtime"


def test_no_identity_reaches_a_committed_byte(corpus):
    """Counts only (the bar, §What this run may NOT do, item 6)."""
    blob = b"".join(p.read_bytes() for p in store_mod.iter_shard_paths(corpus)).lower()
    for token in (b"example.org", b"alice", b"bob", b"carol", b"dave", b"erin", b"frank", b"someone"):
        assert token not in blob, token


def test_no_repository_writes_no_counts(tmp_path):
    root = _configure(tmp_path)
    _write(root, "docs/a.md", "# A\n\ncold chain\n")
    _ingest(root)
    record = _records(root)["docs/a.md"]
    assert "authors" not in record and "commits" not in record and "mtime" not in record


def test_a_shallow_clone_keeps_mtime_and_writes_no_counts(tmp_path):
    source = _history(tmp_path / "source")
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", "--depth", "1", f"file://{source}", str(clone))
    _ingest(_configure(clone))
    records = _records(clone)
    assert records and all("authors" not in r and "commits" not in r for r in records.values())
    assert all("mtime" in r for r in records.values())


def test_a_delta_run_equals_a_full_run(tmp_path):
    root = _corpus(tmp_path)
    before = {p.name: p.read_bytes() for p in store_mod.iter_shard_paths(root)}
    _ingest(root)
    assert {p.name: p.read_bytes() for p in store_mod.iter_shard_paths(root)} == before
    _ingest(root, full=True)
    assert {p.name: p.read_bytes() for p in store_mod.iter_shard_paths(root)} == before


# -- the prior -----------------------------------------------------------------


def test_the_default_is_off():
    """Unmeasured: it ships at `0.0` pending the verdict."""
    assert template_tune().authority_weight == 0.0


def test_off_never_reads_the_counts_and_is_the_engine_before_the_key(corpus, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("the authority counts were read with the prior off")

    monkeypatch.setattr(rank_mod, "authority_product", boom)
    for q in QUESTIONS:
        for force_scan in (True, False):
            results, _ = run_query(corpus, q, 10, force_scan=force_scan, tune=tuned(authority_weight=0.0), use_tune=True)
            assert _payload(results) == _payload(scan_ask(corpus, q, top=10, scoring=scoring()))


def test_off_leaves_weighting_trivial():
    assert Weighting(authority_weight=0.0).trivial
    assert Weighting(authority_weight=0.0).maximum == 1.0
    assert Weighting(authority_weight=0.0).of({"loc": "x", "authors": 9, "commits": 9}) == 1.0


@pytest.mark.parametrize("weight", [0.1, 0.3])
def test_on_scales_by_exactly_one_plus_w_f(corpus, weight):
    q = "cold chain"
    off = {r.loc: r.score for r in run_query(corpus, q, 20, tune=tuned(authority_weight=0.0), force_scan=True, use_tune=True)[0]}
    on = {r.loc: r.score for r in run_query(corpus, q, 20, tune=tuned(authority_weight=weight), force_scan=True, use_tune=True)[0]}
    assert set(on) == set(off), "a prior re-orders; it never adds or drops a document"
    for loc, score in off.items():
        authors, commits = EXPECTED.get(loc, (1, 1))
        expected = score * (1.0 + weight * (1.0 - 1.0 / (authors * commits)))
        assert on[loc] == pytest.approx(expected, rel=1e-12), loc
    assert on["docs/draft-cold-chain.md"] == off["docs/draft-cold-chain.md"], "1 · 1 is untouched exactly"


def test_the_factor_and_the_supremum():
    w = Weighting(authority_weight=0.5)
    assert w.authority_for({"authors": 1, "commits": 1}) == 1.0
    assert w.authority_for({"authors": 1, "commits": 2}) == 1.25
    assert w.authority_for({"authors": 3, "commits": 4}) == 1.0 + 0.5 * (1.0 - 1.0 / 12)
    for bad in ({}, {"authors": 2}, {"authors": 0, "commits": 3}, {"authors": True, "commits": 3}, {"authors": 2.0, "commits": 3}):
        assert w.authority_for(bad) == 1.0, bad
    assert w.maximum == 1.5
    stacked = Weighting(priority=(("docs/", 2.0),), doctype=DOCTYPE, intent_type="procedure", intent_factor=1.1, authority_weight=0.5)
    assert stacked.maximum == 2.0 * 1.1 * 1.5
    record = {"loc": "docs/40-procedure-x.md", "authors": 10, "commits": 50}
    assert stacked.of(record) == 2.0 * 1.1 * (1.0 + 0.5 * (1.0 - 1.0 / 500))
    assert stacked.of(record) < stacked.maximum


@pytest.mark.parametrize("weight", [0.0, 0.1, 0.2, 0.3, 0.5])
@pytest.mark.parametrize("q", QUESTIONS)
@pytest.mark.parametrize("stack", ["none", "priority", "intent"])
def test_the_scan_and_the_accelerator_agree(corpus, q, weight, stack):
    more = {"priority": PRIORITY} if stack == "priority" else {}
    if stack == "intent":
        more = {"intent_weight": 0.1, "doctype": DOCTYPE}
    tune = tuned(authority_weight=weight, **more)
    scan_results, path_a = run_query(corpus, "how do I " + q if stack == "intent" else q, 10, force_scan=True, tune=tune, use_tune=True)
    fast_results, path_b = run_query(corpus, "how do I " + q if stack == "intent" else q, 10, force_scan=False, tune=tune, use_tune=True)
    assert (path_a, path_b) == ("scan", "accelerator")
    assert _payload(fast_results) == _payload(scan_results)


@pytest.mark.parametrize("weight", [0.1, 0.5])
def test_the_accelerator_bound_survives_top_one(corpus, weight):
    """`top = 1` is where a ceiling that forgot `1 + w` would skip the winner."""
    tune = tuned(authority_weight=weight)
    for q in QUESTIONS:
        a, _ = run_query(corpus, q, 1, force_scan=True, tune=tune, use_tune=True)
        b, _ = run_query(corpus, q, 1, force_scan=False, tune=tune, use_tune=True)
        assert _payload(a) == _payload(b), q


# -- the CLI: lexical, --why ----------------------------------------------------

ON_TUNE = tune_text(ranking={"authority_weight": 0.5})
OFF_TUNE = tune_text(ranking={"authority_weight": 0.0})


def _cli(root: Path, *argv: str) -> dict:
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *argv, "--json", "--top", "10"],
        capture_output=True, text=True, encoding="utf-8", cwd=root, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _rows(payload: dict):
    return [(r["id"], round(r["score"], 9)) for r in payload["results"]]


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    base = tmp_path_factory.mktemp("authority-cli")
    return _corpus(base / "on", ON_TUNE), _corpus(base / "off", OFF_TUNE)


def test_lexical_never_applies_it(pair):
    on, off = pair
    q = "cold chain"
    assert _rows(_cli(on, "lexical", q)) == _rows(_cli(off, "lexical", q))
    assert _rows(_cli(on, "ask", q)) != _rows(_cli(off, "ask", q)), "the arm moves ask"


def test_why_names_the_prior_on_a_document_it_moved_and_only_then(pair):
    on, off = pair
    q = "cold chain"
    docs = {d["loc"]: d for d in _cli(on, "ask", q, "--why")["derivation"]["documents"]}
    assert docs["docs/maintained-cold-chain.md"]["authority"] == {
        "authors": 3, "commits": 4, "factor": 1.0 + 0.5 * (1.0 - 1.0 / 12),
    }
    assert docs["docs/pair-cold-chain.md"]["authority"] == {"authors": 1, "commits": 2, "factor": 1.25}
    assert "authority" not in docs["docs/draft-cold-chain.md"], "a 1 · 1 document is not moved"
    off_docs = _cli(off, "ask", q, "--why")["derivation"]["documents"]
    assert off_docs and all("authority" not in d for d in off_docs)


# -- the Node reader -----------------------------------------------------------


def _node(root: Path, verb: str, query: str) -> list:
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), verb, query, "--json", "--top", "10"],
        capture_output=True, text=True, encoding="utf-8", cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    return [(r["id"], round(r["score"], 9)) for r in json.loads(proc.stdout)["results"]]


@pytest.mark.parametrize("weight", [0.0, 0.3])
@pytest.mark.parametrize("verb", ["ask", "lexical"])
def test_node_ranks_identically(tmp_path, weight, verb):
    root = _corpus(tmp_path, tune_text(ranking={"authority_weight": weight}))
    for q in QUESTIONS:
        assert _node(root, verb, q) == _rows(_cli(root, verb, q)), q


def test_node_reads_the_factor_identically():
    records = [
        {"authors": 1, "commits": 1}, {"authors": 1, "commits": 2}, {"authors": 3, "commits": 4},
        {"authors": 7, "commits": 33}, {}, {"authors": 2}, {"authors": 0, "commits": 2},
    ]
    proc = subprocess.run(
        ["node", "--input-type=module", "-e",
         'import { Weighting } from "./node/src/query/rank.mjs";'
         f"const rs = {json.dumps(records)};"
         "const out = [0.1, 0.2, 0.3, 0.5].map((w) => rs.map((r) => new Weighting({ authorityWeight: w }).authorityFor(r)));"
         "console.log(JSON.stringify(out));"],
        capture_output=True, text=True, encoding="utf-8", cwd=ENGINE,
    )
    assert proc.returncode == 0, proc.stderr
    expected = [[Weighting(authority_weight=w).authority_for(r) for r in records] for w in (0.1, 0.2, 0.3, 0.5)]
    assert json.loads(proc.stdout) == expected
