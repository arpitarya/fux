"""W-168 step 9 — the intent → doc-type prior: the lexicon, `[doctype]`, the
prior, both readers.

What the frozen bar requires of the build
([PRE-REGISTRATION](../../work/regression/2026-09-28-intent-prior/PRE-REGISTRATION.md)
§The mechanism), one test per row:

- the engine's lexicon IS the frozen tag's, pattern for pattern and in order;
- a glob matches the whole location, `*` crosses `/`, the longest pattern wins;
- `[doctype]` accepts only the three types, sorted longest-first;
- `intent_weight = 0.0`, or no `[doctype]`, never consults the lexicon and is
  the engine before the key;
- on, a document of the preferred type is scaled by exactly `1 + w`, and
  nothing else moves;
- the scan and the accelerator agree, `[priority]` stacked on top included;
- `fux lexical` never applies it;
- `--why` names it when it ran, and is unchanged when it did not;
- the Node reader reads intent, matches globs and ranks identically.
"""

from __future__ import annotations

from l12_fixtures import scoring, template_tune, tune_text, tuned, write_config
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fux.constants import fixed, table
from fux.derive import build
from fux.errors import FuxError
from fux.ingest.run import run
from fux.query import intent as intent_mod
from fux.query import run_query
from fux.query.rank import Weighting
from fux.query.scan import ask as scan_ask

ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"
TAG_SCRIPT = ENGINE / "work" / "regression" / "2026-09-28-intent-prior" / "evidence" / "tag_intent.py"

DOCTYPE = (
    ("*-procedure-*", "procedure"),
    ("*-reference-*", "reference"),
    ("*-decision-*", "decision"),
)

FILES = {
    "docs/40-procedure-dry-ice.md": "# Dry ice at the dock\n\nHow to top up a reefer with dry ice: gloves, chest, scoop.\n",
    "docs/41-decision-dry-ice.md": "# Dry ice rules\n\nWhy we banned dry ice from the vaccine room: carbon dioxide builds up.\n",
    "docs/42-reference-dry-ice.md": "# Dry ice terms\n\nDry ice is solid carbon dioxide; a dry ice chest holds 50 kg.\n",
    "docs/card-dry-ice.md": "# Dry ice card\n\nDry ice at dock 5: gloves on, chest shut.\n",
}
for _i in range(8):
    FILES[f"docs/filler-{_i:02d}.md"] = f"# Filler {_i}\n\nfiller body text number {_i}\n"

QUESTIONS = (
    "how do I top up dry ice",
    "why was dry ice banned",
    "what is dry ice",
    "dry ice chest",
)


def _corpus(root: Path, tune: str | None = None) -> Path:
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    for rel, text in FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(root)
    build(root)
    if tune is not None:
        (root / ".fux" / "tune.toml").write_text(tune, encoding="utf-8")
        write_config(root)
    return root


@pytest.fixture
def corpus(tmp_path):
    return _corpus(tmp_path)


def _payload(results):
    return [(r.id, round(r.score, 9)) for r in results]


def _on(weight: float, **more):
    return tuned(intent_weight=weight, doctype=DOCTYPE, **more)


# -- the lexicon ---------------------------------------------------------------


def _frozen_tag():
    spec = importlib.util.spec_from_file_location("tag_intent", TAG_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_lexicon_is_the_frozen_tag_pattern_for_pattern():
    """The tag and the mechanism cannot drift apart: a different lexicon
    measures a different question set than the one the bar was frozen on."""
    frozen = _frozen_tag().CUES
    assert fixed("intent", "order") == list(frozen)
    for name, patterns in frozen.items():
        assert fixed("intent", name) == patterns


@pytest.mark.parametrize("q", [
    "How do I seal a truck", "  WHY was it banned", "what is a trip bag", "Define M1",
    "what's the rule", "whats the rule", "what does amber mean here", "steps to check a logger",
    "why\tdid we", "how\ncan we", "no cue at all", "what was the rationale for 18 h",
    "somewhy not", "howdy", "",
])
def test_the_engine_reads_intent_as_the_frozen_tag_does(q):
    assert intent_mod.intent_of(q) == _frozen_tag().intent(" ".join(q.split()))


def test_each_intent_prefers_one_type():
    assert table("intent.type") == {"procedure": "procedure", "rationale": "decision", "reference": "reference"}
    assert intent_mod.TYPES == {"procedure", "decision", "reference"}


# -- the glob ------------------------------------------------------------------


@pytest.mark.parametrize("pattern,loc,expected", [
    ("*-decision-*", "seed/05-decision-telematics.md", True),
    ("*-decision-*", "seed/decision.md", False),
    ("docs/*", "docs/a/b.md", True),
    ("*.md", "a.md.txt", False),
    ("a?c", "abc", True),
    ("a?c", "ac", False),
    ("a?c", "aéc", True),
    ("*", "", True),
    ("", "x", False),
    ("*a*b*", "xxaxxbxx", True),
    ("*a*b", "ab_ba", False),
])
def test_a_glob_matches_the_whole_location(pattern, loc, expected):
    assert intent_mod.glob_match(pattern, loc) is expected


def test_the_longest_pattern_wins_whatever_the_file_order(tmp_path):
    text = tune_text(doctype={"*-decision-*": "decision", "*/special-decision-*": "reference"})
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "tune.toml").write_text(text, encoding="utf-8")
    from fux.tune import load

    doctype = load(tmp_path, enabled=True).doctype
    assert doctype == (("*/special-decision-*", "reference"), ("*-decision-*", "decision"))
    assert intent_mod.type_for("a/special-decision-x.md", doctype) == "reference"
    assert intent_mod.type_for("a/other-decision-x.md", doctype) == "decision"


def test_a_doctype_outside_the_three_is_refused(tmp_path):
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "tune.toml").write_text(tune_text(doctype={"*x*": "runbook"}), encoding="utf-8")
    from fux.tune import load

    with pytest.raises(FuxError, match=r'\[doctype\] "\*x\*" must be one of'):
        load(tmp_path, enabled=True)


# -- the prior -----------------------------------------------------------------


def test_the_default_is_off_and_the_template_declares_no_type():
    assert template_tune().intent_weight == 0.0
    assert template_tune().doctype == ()


def test_off_never_consults_the_lexicon(corpus, monkeypatch):
    """`0.0` — or a weight with no `[doctype]` — is the engine before the key,
    and the cheapest proof is that the lexicon is never read."""

    def boom(*_a, **_k):
        raise AssertionError("the intent lexicon was consulted with the prior off")

    monkeypatch.setattr(intent_mod, "intent_of", boom)
    for tune in (tuned(intent_weight=0.0, doctype=DOCTYPE), tuned(intent_weight=0.5)):
        for q in QUESTIONS:
            for force_scan in (True, False):
                results, _ = run_query(corpus, q, 10, force_scan=force_scan, tune=tune)
                assert _payload(results) == _payload(scan_ask(corpus, q, top=10, scoring=scoring()))


@pytest.mark.parametrize("q,preferred", [
    ("how do I top up dry ice", "docs/40-procedure-dry-ice.md"),
    ("why was dry ice banned", "docs/41-decision-dry-ice.md"),
    ("what is dry ice", "docs/42-reference-dry-ice.md"),
])
def test_on_scales_the_preferred_type_by_exactly_one_plus_w(corpus, q, preferred):
    off = {r.loc: r.score for r in run_query(corpus, q, 20, tune=tuned(intent_weight=0.0, doctype=DOCTYPE))[0]}
    on = {r.loc: r.score for r in run_query(corpus, q, 20, tune=_on(0.3))[0]}
    assert set(on) == set(off), "a prior re-orders; it never adds or drops a document"
    for loc, score in off.items():
        expected = score * 1.3 if loc == preferred else score
        assert on[loc] == pytest.approx(expected, rel=1e-12), loc


def test_a_question_with_no_cue_is_untouched(corpus):
    q = "dry ice chest"
    off, _ = run_query(corpus, q, 10, tune=tuned(intent_weight=0.0, doctype=DOCTYPE))
    on, _ = run_query(corpus, q, 10, tune=_on(0.5))
    assert _payload(on) == _payload(off)


def test_the_supremum_is_the_product_of_both_multipliers():
    """Restored with the second multiplier: a document `[priority]` promotes can
    also be the preferred type, and the accelerator's bound must survive it."""
    w = Weighting(priority=(("docs/", 2.0),), doctype=DOCTYPE, intent_type="decision", intent_factor=1.5)
    assert w.maximum == 3.0
    assert w.of({"loc": "docs/41-decision-dry-ice.md"}) == 3.0
    assert w.of({"loc": "docs/40-procedure-dry-ice.md"}) == 2.0
    assert Weighting(doctype=DOCTYPE, intent_type=None, intent_factor=1.5).trivial
    assert Weighting(doctype=(), intent_type="decision", intent_factor=1.5).trivial


@pytest.mark.parametrize("weight", [0.1, 0.2, 0.3, 0.5])
@pytest.mark.parametrize("q", QUESTIONS)
@pytest.mark.parametrize("priority", [(), (("docs/41", 0.5), ("docs/4", 2.0))])
def test_the_scan_and_the_accelerator_agree(corpus, q, weight, priority):
    tune = _on(weight, priority=priority)
    scan_results, path_a = run_query(corpus, q, 10, force_scan=True, tune=tune)
    fast_results, path_b = run_query(corpus, q, 10, force_scan=False, tune=tune)
    assert (path_a, path_b) == ("scan", "accelerator")
    assert _payload(fast_results) == _payload(scan_results)


# -- the CLI: lexical, --why ----------------------------------------------------

ON_TUNE = tune_text(ranking={"intent_weight": 0.5}, doctype=dict(DOCTYPE))
OFF_TUNE = tune_text(ranking={"intent_weight": 0.0}, doctype=dict(DOCTYPE))


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


def test_lexical_never_applies_it(tmp_path):
    on = _corpus(tmp_path / "on", ON_TUNE)
    off = _corpus(tmp_path / "off", OFF_TUNE)
    q = "why was dry ice banned"
    assert _rows(_cli(on, "lexical", q)) == _rows(_cli(off, "lexical", q))
    assert _rows(_cli(on, "ask", q)) != _rows(_cli(off, "ask", q)), "the arm moves ask"


def test_why_names_the_prior_when_it_ran_and_only_then(tmp_path):
    on = _corpus(tmp_path / "on", ON_TUNE)
    off = _corpus(tmp_path / "off", OFF_TUNE)
    q = "why was dry ice banned"
    why_on = _cli(on, "ask", q, "--why")["derivation"]
    assert why_on["intent"] == {"cue": "rationale", "type": "decision", "weight": 0.5}
    factors = {d["loc"]: d["intent_factor"] for d in why_on["documents"]}
    assert factors["docs/41-decision-dry-ice.md"] == 1.5
    assert factors["docs/42-reference-dry-ice.md"] == 1.0
    why_off = _cli(off, "ask", q, "--why")["derivation"]
    assert "intent" not in why_off
    assert all("intent_factor" not in d for d in why_off["documents"])


# -- the Node reader -----------------------------------------------------------


def _node_eval(script: str):
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, encoding="utf-8", cwd=ENGINE,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_node_reads_intent_and_matches_globs_identically():
    questions = [
        "How do I seal a truck", "  WHY was it banned", "what's the rule", "what does x mean",
        "define M1", "howdy", "whyé", "HOW TO", "what\tis this", "",
    ]
    globs = [
        ["*-decision-*", "seed/05-decision-x.md"], ["a?c", "a\U0001F600c"], ["*a*b", "ab_ba"],
        ["docs/*", "docs/a/b.md"], ["?", "\U0001F600"],
    ]
    node = _node_eval(
        'import { intentOf, globMatch } from "./node/src/query/intent.mjs";'
        f"const qs = {json.dumps(questions)}; const gs = {json.dumps(globs)};"
        "console.log(JSON.stringify([qs.map(intentOf), gs.map(([p, t]) => globMatch(p, t))]));"
    )
    assert node == [
        [intent_mod.intent_of(q) for q in questions],
        [intent_mod.glob_match(p, t) for p, t in globs],
    ]


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
    root = _corpus(tmp_path, tune_text(ranking={"intent_weight": weight}, doctype=dict(DOCTYPE)))
    for q in QUESTIONS:
        assert _node(root, verb, q) == _rows(_cli(root, verb, q)), q
