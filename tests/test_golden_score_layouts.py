"""W-218 — the scorer takes generation-2 set names, and the recipe finds a flat hand-off.

🔴 **Synthetic hand-offs and a synthetic key, under `tmp_path`, and nothing
else.** No test here opens the sealed directory, and none calls `score.main`
past its guards: the set name is tested at `set_label` and `build_payload`, and
the layouts at `handoffs.discover`, which reads no key. If this file ever needs
a real key, or needs the tripwire lifted, it has been written wrong.

**The two defects it pins:**

1. `--set` was `type=int`, so `--set 2-u` exited in argparse, and the
   workaround wrote `"set": 2` — the name of a RETIRED generation-1 set — into a
   file called `set-2-u.json`.
2. The recipe globbed `evidence/*/rung-*/` and `evidence/rung-*/` only, so the
   `set-2-u` baseline, filed flat at `evidence/handoff-set-2-u.jsonl`, was never
   found.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools" / "golden-score"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"golden_{name}", TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scorer():
    return _load("score")


@pytest.fixture(scope="module")
def handoffs():
    return _load("handoffs")


SYNTHETIC_KEY = {"q001": {"id": "q001", "relevant": ["docs/a.md"], "primary": "docs/a.md", "answerable": True}}
SYNTHETIC_ROWS = {"q001": {"id": "q001", "ranked": ["docs/a.md"], "band": "strong", "answerable": True}}


# --- 1. the set name ----------------------------------------------------------

@pytest.mark.parametrize("name", ["2-u", "3-x", "1", "12"])
def test_set_label_accepts_both_generations_verbatim(scorer, name):
    assert scorer.set_label(name) == name


@pytest.mark.parametrize("name", ["2u", "2-z", "set-2-u", "", "u", "2-u-1"])
def test_set_label_refuses_anything_else(scorer, name):
    with pytest.raises(argparse.ArgumentTypeError):
        scorer.set_label(name)


@pytest.mark.parametrize("name", ["2-u", "1"])
def test_the_output_carries_the_set_name_verbatim(scorer, name):
    """🔴 The mislabel W-218 exists for: `"set": 2` in a `set-2-u.json`."""
    payload = scorer.build_payload(SYNTHETIC_ROWS, SYNTHETIC_KEY, rung="rung-01000", arm="single", set_name=name)
    assert payload["set"] == name and isinstance(payload["set"], str)
    assert payload["totals"]["hit@1"] == 1 and payload["partial"] is False


def test_argparse_takes_2_u_where_it_used_to_exit(scorer, monkeypatch):
    """Parsed, never run: `main` is stopped at its first guard, which is the
    Claude-environment tripwire, and that refusal is asserted as the outcome."""
    monkeypatch.setenv("CLAUDECODE", "1")
    rc = scorer.main(["--handoff", "h", "--key", "k", "--out", "o",
                      "--rung", "rung-01000", "--arm", "single", "--set", "2-u"])
    assert rc == 2, "argparse accepted 2-u and the tripwire, not argparse, refused"


# --- 2. the layouts -----------------------------------------------------------

def _handoff(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(SYNTHETIC_ROWS["q001"]) + "\n", encoding="utf-8")
    return path


def test_the_two_nested_layouts_are_still_found(handoffs, tmp_path):
    ev = tmp_path / "evidence"
    _handoff(ev / "v1" / "rung-00100" / "handoff-set-1.jsonl")
    _handoff(ev / "rung-01000" / "handoff-set-3.jsonl")
    got = [(a, r, s) for _, a, r, s in handoffs.discover(tmp_path)]
    assert got == [("v1", "rung-00100", "1"), ("single", "rung-01000", "3")]


def test_a_flat_handoff_takes_its_rung_from_the_argument(handoffs, tmp_path):
    _handoff(tmp_path / "evidence" / "handoff-set-2-u.jsonl")
    (tmp_path / "evidence" / "predictions-set-2-u.jsonl").write_text("{}\n", encoding="utf-8")
    got = handoffs.discover(tmp_path, "rung-01000")
    assert [(a, r, s) for _, a, r, s in got] == [("single", "rung-01000", "2-u")]


def test_a_flat_handoff_takes_its_rung_from_the_preregistration(handoffs, tmp_path):
    _handoff(tmp_path / "evidence" / "handoff-set-2-u.jsonl")
    (tmp_path / "PRE-REGISTRATION.md").write_text(
        "---\ntype: Pre-Registration\n---\n\n# capture on `rung-01000`\n\nOne rung, `rung-01000`.\n",
        encoding="utf-8")
    assert handoffs.discover(tmp_path)[0][2] == "rung-01000"


def test_frontmatter_rung_wins_over_the_body(handoffs, tmp_path):
    _handoff(tmp_path / "evidence" / "handoff-set-2-u.jsonl")
    (tmp_path / "PRE-REGISTRATION.md").write_text(
        "---\nrung: rung-00500\n---\n\nCompared with rung-01000 and rung-10000.\n", encoding="utf-8")
    assert handoffs.discover(tmp_path)[0][2] == "rung-00500"


@pytest.mark.parametrize("prereg", [None, "Compared across rung-00100 and rung-01000.\n", "No rung here.\n"])
def test_a_flat_handoff_whose_rung_would_be_guessed_is_refused(handoffs, tmp_path, prereg):
    """🔴 A wrong rung files a number under an index it was not measured on."""
    _handoff(tmp_path / "evidence" / "handoff-set-2-u.jsonl")
    if prereg is not None:
        (tmp_path / "PRE-REGISTRATION.md").write_text(prereg, encoding="utf-8")
    with pytest.raises(SystemExit, match="refusing"):
        handoffs.discover(tmp_path)


def test_a_malformed_rung_argument_is_refused(handoffs, tmp_path):
    _handoff(tmp_path / "evidence" / "handoff-set-2-u.jsonl")
    with pytest.raises(SystemExit, match="rung-NNNNN"):
        handoffs.discover(tmp_path, "01000")


def test_a_handoff_that_names_no_set_is_refused(handoffs, tmp_path):
    _handoff(tmp_path / "evidence" / "rung-01000" / "handoff-set-two.jsonl")
    with pytest.raises(SystemExit, match="set-<n>"):
        handoffs.discover(tmp_path)


def test_the_recipe_delegates_discovery_and_passes_the_set_name_through():
    """The recipe can't be run from a test (it starts the scorer), so its
    wiring is read: discovery comes from handoffs.py, and the set name reaches
    both the key path and `--set` unchanged."""
    recipe = (REPO / "justfile").read_text(encoding="utf-8")
    body = recipe[recipe.index("golden-score run"):recipe.index("scored $n hand-off(s)")]
    assert "tools/golden-score/handoffs.py" in body
    assert 'set-${s}.jsonl' in body and '--set "$s"' in body
    assert "evidence/*/rung-*/handoff-set-" not in body, "discovery lives in one place"
