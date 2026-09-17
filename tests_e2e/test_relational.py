"""Relational eval: the graph lane's surfaces, measured through the real CLI.

Retrieval metrics are blind to `explain`, `graph` and `path` — they score
passages, and these verbs return relationships. This is the instrument for
those, ported from `archive/v0.26/tests_e2e/test_relational.py` with its
corpus and its cases.

The port's one adaptation — the edge vocabulary, `references`/`cites` → `ref`
— is stated in `eval/README-relational.md` rather than left to be discovered.
The archived file is **named, never cited**: this test and its fixture are
live files in this tree, and nothing here reads out of `archive/`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux.query import RELATED_HEADING

EVAL_DIR = Path(__file__).parent / "eval"
PAIRS = EVAL_DIR / "relational.jsonl"
CORPUS = EVAL_DIR / "relational"


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True,
    )


def load_pairs(kind: str) -> list[dict]:
    return [
        entry
        for line in PAIRS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for entry in [json.loads(line)]
        if entry["kind"] == kind
    ]


@pytest.fixture(scope="module")
def linked(tmp_path_factory) -> Path:
    proj = tmp_path_factory.mktemp("relational")
    shutil.copytree(CORPUS / "docs", proj / "docs")
    (proj / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = proj / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (proj / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    _run(proj, "ingest")
    return proj


@pytest.mark.parametrize("case", load_pairs("path"), ids=lambda c: f"{c['from']}->{c['to']}")
def test_expected_paths_are_found(linked, case):
    payload = json.loads(
        _run(linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"])).stdout
    )
    assert payload["paths"], f"no route {case['from']} → {case['to']}"
    best = payload["paths"][0]
    assert best["hops"][0]["kind"] == case["expect"]
    assert best["hops"][-1]["dst"] == f"file:{case['to']}"
    assert 0 < best["reliability"] <= 1.0


@pytest.mark.parametrize("case", load_pairs("nopath"), ids=lambda c: f"{c['from']}-x-{c['to']}")
def test_absent_routes_stay_absent(linked, case):
    """Honest emptiness is a behaviour worth pinning, not just a fallback."""
    payload = json.loads(
        _run(linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"])).stdout
    )
    assert payload["paths"] == []


@pytest.mark.parametrize("case", load_pairs("neighbour"), ids=lambda c: c["doc"])
def test_explain_lists_the_expected_edges(linked, case):
    """Exactly these — a superset is as wrong as a subset."""
    payload = json.loads(_run(linked, "explain", case["doc"], "--json").stdout)
    assert {e["dst"] for e in payload["edges"]} == set(case["expect"])


@pytest.mark.parametrize("case", load_pairs("graph"), ids=lambda c: c["query"])
def test_graph_surfaces_the_expected_node(linked, case):
    payload = json.loads(_run(linked, "graph", case["query"], "--json").stdout)
    assert case["expect_node"] in {n["path"] for n in payload["nodes"]}


def test_relational_surfaces_are_deterministic(linked):
    """L3 at the surface: same corpus, same bytes, every run."""
    for args in (
        ("path", "docs/adr-storage.md", "docs/rota-oncall.md", "--json", "--hops", "2"),
        ("explain", "docs/adr-storage.md", "--json"),
        ("graph", "storage engine selection", "--json"),
    ):
        first = _run(linked, *args).stdout
        assert _run(linked, *args).stdout == first


def test_reliability_decays_with_distance(linked):
    """A two-hop route must be less reliable than a one-hop one."""
    def best(to: str) -> float:
        payload = json.loads(
            _run(linked, "path", "docs/adr-storage.md", to, "--json", "--hops", "2").stdout
        )
        return payload["paths"][0]["reliability"]

    assert best("docs/rota-oncall.md") < best("docs/runbook-rollback.md")


def test_the_two_candidate_paths_still_agree_with_a_graph_tier(linked):
    """**This test was `test_the_graph_lane_does_not_move_ask`, and W-161
    inverted it deliberately** — SR-GRAPH's *`ask` is untouched* was superseded
    by the compare doc Arpit ratified on 2026-09-13.

    What it asserted — *the graph plane must not reach `ask`* — is now false by
    design. What survives is the half that was always the real content: **the
    accelerator and the scan must return the same bytes**, tier included. The
    graph stage runs after both and reads the same derived plane, so a
    divergence here means the tier is reading something path-dependent, which
    is the differential law's business rather than the graph lane's.

    ⚠ **Deleting it instead would have lost that**, and the composition tests
    below do not cover it: they compare verbs, not candidate paths.
    """
    _run(linked, "build")
    for query in ("storage engine selection", "rollback", "catering"):
        scanned = _run(linked, "ask", query, "--json").stdout
        accelerated = _run(linked, "ask", query, "--json", "--fast").stdout
        assert accelerated == scanned, query


def test_ask_is_lexical_when_the_graph_tier_is_off(linked):
    """**Composition test 1** (W-161 DoD 1): `ask`'s lexical stage IS `lexical`.

    With both tier booleans off, `ask` must be `fux lexical` byte for byte —
    not approximately, and not only in the ranking. That is what makes
    `lexical` a baseline: every ranking verdict in this repository compares
    something against *the words alone*, and if `ask` minus the tier were not
    exactly `lexical` then the baseline would be measuring a third thing.
    """
    _run(linked, "build")
    off = "[graph]\nask_boost = false\nask_related = false\n"
    (linked / ".fux" / "tune.toml").write_text(off, encoding="utf-8")
    try:
        for query in ("storage engine selection", "rollback", "catering"):
            for extra in ((), ("--json",), ("--top", "3"), ("--band",)):
                ask = _run(linked, "ask", query, *extra).stdout
                lexical = _run(linked, "lexical", query, *extra).stdout
                assert ask == lexical, (query, extra)
    finally:
        (linked / ".fux" / "tune.toml").unlink()


def test_lexical_ignores_a_tune_that_turns_the_tier_on(linked):
    """🔴 **The freeze, tested where it could actually be lost.**

    `fux lexical` is the lexical core and has no graph tier *by definition*.
    A repository whose `.fux/tune.toml` turns the tier on must not be able to
    make the frozen baseline verb stop being a baseline — otherwise every
    verdict that cites `lexical` as its control is measuring whatever that
    repo's config happened to say.

    The tier is forced off in `_ask_shaped`, not left to the caller, and this
    is the assertion that would fail if someone moved that decision outwards.
    """
    _run(linked, "build")
    (linked / ".fux" / "tune.toml").write_text(
        "[graph]\nask_boost = true\nask_related = true\n", encoding="utf-8"
    )
    try:
        for query in ("storage engine selection", "rollback", "catering"):
            payload = json.loads(_run(linked, "lexical", query, "--json").stdout)
            assert "related" not in payload, query
            assert not any(r["boosted"] for r in payload["results"]), query
    finally:
        (linked / ".fux" / "tune.toml").unlink()


def test_ask_related_is_the_walk_over_lexical_top_k(linked):
    """**Composition test 2** (W-161 DoD 1): `ask`'s `related` ≡ `graph` fed
    `lexical`'s top-k, minus everything the words already matched.

    ⚠ **The two are NOT simply equal, and the difference is the split rule
    itself.** `graph --seed` returns every walked non-seed node; `related` is
    that list with two filters — a node already in `ask`'s retrieval window is
    a boosted candidate rather than a neighbour, and a node whose committed
    record holds a query term is a lexical match that ranked low rather than a
    document the words could not reach. So what this asserts is **containment
    in order**: every `related` id appears in the walk, in the walk's order.

    A test asserting equality would be asserting the filters do nothing.
    """
    _run(linked, "build")
    for query in ("storage engine selection", "rollback", "catering"):
        payload = json.loads(_run(linked, "ask", query, "--json").stdout)
        related = [r["id"] for r in payload.get("related", [])]
        if not related:
            continue
        seeds = [
            n["id"]
            for n in json.loads(_run(linked, "graph", query, "--json").stdout)["nodes"]
            if n["role"] == "seed"
        ]
        # ⚠ **The `ask` walk's parameters, passed explicitly.** `fux graph`
        # keeps its own defaults — all edge kinds, no hub damping, unbounded
        # hops — because orientation and answering want different walks, and
        # the compare doc ruled they may differ. Comparing against the bare
        # `graph` defaults would be comparing two different walks and calling
        # the difference a composition failure.
        walked = [
            n["id"]
            for n in json.loads(
                _run(
                    linked, "graph", *[a for s in seeds for a in ("--seed", s)],
                    "--kinds", "ref", "--link-idf", "--max-hops", "1", "--json",
                ).stdout
            )["nodes"]
            if n["role"] == "expanded"
        ]
        assert set(related) <= set(walked), (query, related, walked)
        assert related == [i for i in walked if i in set(related)], (query, related, walked)


def test_no_related_row_is_ever_a_result(linked):
    """🔴 **The one invariant the whole tier rests on.**

    A Tier B document has no BM25F score — that is its definition. If one ever
    appeared in `results` it would arrive carrying whatever score the shape
    demanded, and a reader would have no way to tell a document the words
    found from one a link reached. The compare doc rejected interleaving for
    exactly this and the two lists being two objects is the enforcement.
    """
    _run(linked, "build")
    for query in ("storage engine selection", "rollback", "catering"):
        payload = json.loads(_run(linked, "ask", query, "--json").stdout)
        hits = {r["id"] for r in payload["results"]}
        related = {r["id"] for r in payload.get("related", [])}
        assert not (hits & related), (query, hits & related)


def test_no_related_omits_the_tier_entirely(linked):
    """`--no-related` removes the key, in text and in `--json` alike.

    ⚠ **Absent, not empty.** `[]` is what *no neighbours* looks like; an absent
    key is what *you said not to compute it* looks like. A consumer that cannot
    tell those apart cannot tell a corpus with no links from a flag it forgot
    it set — `confidence`-under-`--band`'s shape exactly.
    """
    _run(linked, "build")
    for query in ("storage engine selection", "rollback"):
        assert "related" not in json.loads(
            _run(linked, "ask", query, "--json", "--no-related").stdout
        ), query
        assert RELATED_HEADING not in _run(linked, "ask", query, "--no-related").stdout


def test_a_related_route_only_names_an_edge_kind_the_walk_followed(linked):
    """🔴 **Found on the first real run, against fux's own corpus.**

    With `ask_kinds = "ref"` the route line read `#2 via code` — naming an edge
    the walk was forbidden to follow and had not followed. The walk had reached
    the document through a `ref` edge; the route credited a `code` edge that
    merely happened to exist between the same two documents.

    **A route a reader cannot verify is worse than no route**, and this tier's
    whole claim to honesty is that its provenance can be checked.
    """
    _run(linked, "build")
    for query in ("storage engine selection", "rollback", "catering"):
        payload = json.loads(_run(linked, "ask", query, "--json").stdout)
        for row in payload.get("related", []):
            assert row["route"] == "via the walk" or row["route"].endswith(" via ref"), row


def test_graph_verbs_ask_for_a_build_rather_than_crashing(linked, tmp_path):
    """A repo with a committed index and no derived plane must say so."""
    proj = tmp_path / "unbuilt"
    shutil.copytree(linked, proj, ignore=shutil.ignore_patterns("runtime"))
    shutil.rmtree(proj / ".fux" / "runtime", ignore_errors=True)

    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "explain", "docs/adr-storage.md"],
        cwd=proj, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 1
    assert "fux build" in result.stderr
    assert "Traceback" not in result.stderr


# -- W-140 row 12: a typo must not read as an answer -------------------------


def _run_failing(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )


def test_path_refuses_a_from_that_is_not_in_the_index(linked):
    """🔴 It printed *No route … within N hop(s)* and exited 0.

    A true sentence about a document that does not exist, and byte-identical
    to the answer for two real documents that are genuinely unrelated — so a
    typo read as a finding. `explain` was fixed for exactly this in W-63; the
    verb next door kept the defect.
    """
    result = _run_failing(linked, "path", "docs/does-not-exist.md", "docs/adr-storage.md")
    assert result.returncode == 1
    assert "not in the index (FROM)" in result.stderr


def test_path_names_which_end_was_wrong(linked):
    result = _run_failing(linked, "path", "docs/adr-storage.md", "docs/typo.md")
    assert result.returncode == 1
    assert "not in the index (TO)" in result.stderr


def test_path_still_answers_honestly_for_two_real_unrelated_documents(linked):
    """The control. Refusing a typo must not turn an honest empty into an error."""
    cases = load_pairs("nopath")
    case = cases[0]
    result = _run(linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"]))
    assert json.loads(result.stdout)["paths"] == []


def test_explain_refuses_a_tag_that_does_not_exist(linked):
    """A tag is a node in the plane, so the plane is what knows it.

    The existence check read the committed index, where a tag has no record,
    so `explain tag:typo` fell through to *has no recorded relationships* —
    which reads as *this tag exists and links nowhere*.
    """
    result = _run_failing(linked, "explain", "tag:definitely-not-a-tag")
    assert result.returncode == 1
    assert "is not a tag in this index" in result.stderr


# -- W-160: the two atoms ----------------------------------------------------


def test_lexical_did_not_move_when_ask_grew_a_tier(linked):
    """🔴 **This test WAS `test_lexical_is_byte_identical_to_ask`, and W-161 is
    the change that inverted it** — as W-160 said it would, in this docstring,
    before the tier existed.

    The freeze was never *these two verbs are equal*. It was **`lexical` does
    not move**, and the equality was how that was checkable while the two were
    one body. Now that they have parted, equality is the wrong assertion and
    would have to be deleted; what replaces it is the same property stated
    directly — `lexical` is BM25F, the proximity reranker and `-q` fusion, and
    carries neither of the tier's two marks.

    ⚠ **Text AND `--json`, still, and for W-160's reason.** The first time
    `lexical` ran, the two agreed on every score and differed in their output:
    `lexical` was absent from `output_config.CLI_VERBS`, so `args.sections`
    never resolved and `ask` printed `§` lines where `lexical` printed none.
    Nothing failed. Comparing only `--json` would still have missed it, because
    `headings` is in the payload either way — so both renderings are walked.
    """
    _run(linked, "build")
    for query in ("storage engine selection", "rollback", "catering"):
        for extra in ((), ("--top", "3"), ("--band",), ("--why",)):
            text = _run(linked, "lexical", query, *extra).stdout
            assert RELATED_HEADING not in text, (query, extra)
            assert "(graph" not in text, (query, extra)
        payload = json.loads(_run(linked, "lexical", query, "--json").stdout)
        assert "related" not in payload, query
        assert not any(r["boosted"] or r["route"] for r in payload["results"]), query


def test_lexical_agrees_with_itself_on_both_candidate_paths(linked):
    """`--fast` and `--scan` are asserted byte-identical for `ask`; the frozen
    verb has to inherit that rather than only matching on the default path.

    ⚠ **It compares `lexical` against `lexical`, not against `ask`** — since
    W-161 the two verbs legitimately differ, so the cross-verb form would now
    be asserting the tier does nothing.
    """
    _run(linked, "build")
    assert (
        _run(linked, "lexical", "rollback", "--json", "--fast").stdout
        == _run(linked, "lexical", "rollback", "--json", "--scan").stdout
    )


def test_graph_query_equals_graph_over_lexical_seeds(linked):
    """**`graph "<q>"` is DEFINED as `--seed` over `lexical`'s top-k** (W-160
    DoD 3), and this asserts it rather than assuming it.

    ⚠ **The seed SCORES are deliberately not compared, and the report says
    which column is which.** The query form reports each seed's BM25F score;
    the `--seed` form reports the mass `walk.ppr` will give it, `1/(i+1)`,
    because a document named by hand has a rank and not a ranking. What must
    agree is the seed ids **in order** — the mass follows argument order — and
    every expanded node, score included, because that is the walk's own output.
    """
    _run(linked, "build")
    tune = json.loads(_run(linked, "graph", "rollback", "--json").stdout)
    seeds = [n["id"] for n in tune["nodes"] if n["role"] == "seed"]
    assert len(seeds) > 1, tune["nodes"]

    seeded = json.loads(
        _run(linked, "graph", *[a for s in seeds for a in ("--seed", s)], "--json").stdout
    )
    assert [n["id"] for n in seeded["nodes"] if n["role"] == "seed"] == seeds
    assert [n for n in seeded["nodes"] if n["role"] == "expanded"] == [
        n for n in tune["nodes"] if n["role"] == "expanded"
    ]


def test_the_seed_form_follows_argument_order(linked):
    """Mass by argument order is the contract; reversing the seeds must move the
    walk, or the order is decorative."""
    _run(linked, "build")
    first = _run(linked, "graph", "--seed", "docs/adr-storage.md", "--seed", "docs/runbook-rollback.md", "--json").stdout
    second = _run(linked, "graph", "--seed", "docs/runbook-rollback.md", "--seed", "docs/adr-storage.md", "--json").stdout
    assert first != second


def test_the_exposed_walk_parameters_are_inert_at_their_defaults(linked):
    """W-160 DoD 4, through the real CLI.

    The unit test proves inertness in `walk.ppr`; this proves the CLI resolves
    an absent flag to the inert value rather than to something that merely
    looks like it. Both halves are needed: a flag defaulting to `""` instead of
    `None` would pass the unit test and fail here.
    """
    _run(linked, "build")
    baseline = _run(linked, "graph", "rollback", "--json").stdout
    # Naming every kind must equal naming none — otherwise the filter is doing
    # something beyond filtering, and the likeliest something is reordering the
    # adjacency, which changes float accumulation and therefore the scores.
    assert (
        _run(linked, "graph", "rollback", "--json", "--kinds", "ref,tag,code,supersedes").stdout
        == baseline
    )
    # `iterations = 3` already bounds reach at three hops, so any bound at or
    # above it re-states what the walk does.
    assert _run(linked, "graph", "rollback", "--json", "--max-hops", "99").stdout == baseline


def test_a_walk_parameter_that_is_set_actually_changes_the_walk(linked):
    """The other half: a knob inert at every setting is dead code with a name.

    ⚠ **`--max-hops 1` is NOT asserted here, and the reason is the corpus.**
    This fixture is 8 documents deep-ish and `seed_depth` is 5, so everything
    the walk reaches is already within one hop of some seed and a bound of 1
    cuts nothing — measured, not assumed: the first version of this test
    asserted it and got two identical payloads. The bound is proved on a graph
    built to have depth, in
    `tests/graph/test_walk_parameters_are_inert.py::test_max_hops_cuts_the_far_node_when_tight`.
    Asserting it here instead would have tied a real parameter's proof to a
    fixture that cannot exercise it.
    """
    _run(linked, "build")
    baseline = _run(linked, "graph", "rollback", "--json").stdout
    assert _run(linked, "graph", "rollback", "--json", "--link-idf").stdout != baseline
    # `ref` only drops the `tag:` nodes the default walk reaches.
    refs_only = _run(linked, "graph", "rollback", "--json", "--kinds", "ref").stdout
    assert refs_only != baseline
    assert "tag:" in baseline and "tag:" not in json.dumps(
        [n for n in json.loads(refs_only)["nodes"] if n["role"] == "expanded"]
    )


def test_graph_refuses_a_query_and_a_seed_together(linked):
    result = _run_failing(linked, "graph", "rollback", "--seed", "docs/adr-storage.md")
    assert result.returncode == 1
    assert "not both" in result.stderr


def test_graph_refuses_neither_a_query_nor_a_seed(linked):
    result = _run_failing(linked, "graph")
    assert result.returncode == 1
    assert "--seed" in result.stderr


def test_graph_refuses_a_seed_that_is_not_in_the_index(linked):
    """Same *three states, not two* rule `path` was fixed for in W-140 row 12:
    a typo'd seed would otherwise walk from nowhere and report an empty
    neighbourhood, which reads as *this document is isolated*."""
    result = _run_failing(linked, "graph", "--seed", "docs/does-not-exist.md")
    assert result.returncode == 1
    assert "not in the index" in result.stderr


def test_kinds_refuses_a_kind_that_does_not_exist(linked):
    result = _run_failing(linked, "graph", "rollback", "--kinds", "reference")
    assert result.returncode == 1
    assert "not an edge kind" in result.stderr
