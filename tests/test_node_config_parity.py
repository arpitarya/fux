"""The Node reader's transcribed CONSTANTS are held equal to Python's.

`node/src/config/{tune,output}.mjs` and `node/src/decode/registry.mjs` carry
key sets, defaults and glob lists that `src/fux/` also carries. The differential
arm cannot catch a drift between them, and that is not a gap in the arm — it is
what the arm structurally is:

- A **key set** drift only shows on a corpus whose `.fux/tune.toml` actually
  sets the drifted key, and every golden rung's tune is all-defaults.
- A **refusal** drift never shows at all. A repository whose config one reader
  refuses and the other accepts does not produce two rankings to compare; it
  produces an answer on one side and an error on the other, and the arm's own
  harness reports that as a crash rather than as a finding.

So these are equality tests, in the shape `tests/test_mcp.py` already uses for
`node/mcp-tools.json` and `tests/test_cli.py` for the `pii.toml` path literal:
**one authority in Python, one transcription in JS, and a test between them.**

W-107 R5 / ADR-NODE-SEARCH decision 8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_SRC = ROOT / "node" / "src"


def _source(rel: str) -> str:
    return (NODE_SRC / rel).read_text(encoding="utf-8")


def _js_string_list(source: str, name: str) -> list[str]:
    """The `["a", "b"]` a `const <name> = [...]` declares, in order."""
    match = re.search(rf"{name}\s*=\s*\[(.*?)\]", source, re.S)
    assert match, f"no `{name} = [...]` in the Node source — the constant was renamed"
    return re.findall(r'"([^"]*)"', match.group(1))


# -- .fux/tune.toml ----------------------------------------------------------


def test_the_node_tune_schema_is_the_python_one():
    """The closed key set, table by table.

    A key Python knows and Node refuses makes a legal file unreadable in one
    runtime; a key Node knows and Python refuses is worse — the file loads,
    the key is silently honoured by one reader, and the two rank differently
    with nothing saying so.
    """
    from fux.tune import _SCHEMA

    source = _source("config/tune.mjs")
    body = re.search(r"const SCHEMA = \{(.*?)\n\};", source, re.S)
    assert body, "no `const SCHEMA = {...}` in config/tune.mjs"

    for table, keys in _SCHEMA.items():
        if not keys:
            continue  # `[priority]` is the open table — no key set to compare
        entry = re.search(rf"(?:{table}|\[INDEX_TABLE\]):\s*\[(.*?)\]", body.group(1), re.S)
        assert entry, f"config/tune.mjs declares no keys for `[{table}]`"
        spelled = re.findall(r'"([^"]*)"', entry.group(1))
        if table == "bm25f":
            # `...FIELD_KEYS` is spread in rather than spelled out, exactly as
            # Python spreads `*_FIELD_KEYS` — compare only what is literal.
            assert spelled == ["k1", "b"], "the [bm25f] scalars drifted"
            continue
        assert spelled == list(keys), f"[{table}] key set differs from tune.py"


@pytest.mark.parametrize(
    "js, py",
    [
        ("k1 = K1", "k1"),
        ("archivedWeight = 1.0", "archived_weight"),
        ("supersededWeight = 1.0", "superseded_weight"),
        ("recencyHalfLifeDays = 0.0", "recency_half_life_days"),
        ("rerankWeight = 0.0", "rerank_weight"),
        ("expandWeight = 0.2", "expand_weight"),
        ("damping = 0.85", "damping"),
        ("iterations = 3", "iterations"),
        ("laziness = 0.5", "laziness"),
        ("hopDecay = 0.5", "hop_decay"),
        ("expandLimit = 10", "expand_limit"),
        ("seedDepth = 5", "seed_depth"),
        ("budget = 8000", "budget"),
        ("perDocFraction = 0.5", "per_doc_fraction"),
        ("minPassageBytes = 120", "min_passage_bytes"),
        ("maxPassageBytes = 4000", "max_passage_bytes"),
    ],
)
def test_every_tune_default_is_spelled_the_same_on_both_sides(js, py):
    """The defaults ARE the answer when the file is absent, which is the common
    case — so a drifted default is a drifted ranking on an untuned repo."""
    from fux.tune import DEFAULT_TUNE

    source = _source("config/tune.mjs")
    assert f"this.{js};" in source, f"`this.{js}` is not in config/tune.mjs any more"
    written = js.split(" = ", 1)[1]
    if written.isidentifier():
        return  # imported from the shared constant, so there is nothing to drift
    assert float(written) == float(getattr(DEFAULT_TUNE, py)), (
        f"`{py}` defaults to {getattr(DEFAULT_TUNE, py)!r} in tune.py and {written} in Node"
    )


# -- .fux/output.toml --------------------------------------------------------


def test_the_node_output_verbs_and_keys_are_the_python_ones():
    from fux.output_config import CLI_VERBS, MCP_KEYS

    source = _source("config/output.mjs")
    body = re.search(r"export const CLI_VERBS = \{(.*?)\n\};", source, re.S)
    assert body, "no `CLI_VERBS` in config/output.mjs"
    for verb, keys in CLI_VERBS.items():
        entry = re.search(rf"\n  {verb}: \[(.*?)\],", body.group(1), re.S)
        assert entry, f"config/output.mjs declares no `{verb}` — an absent verb never resolves `--json`"
        assert re.findall(r'"([^"]*)"', entry.group(1)) == list(keys), f"`{verb}` key set differs"
    assert _js_string_list(source, "export const MCP_KEYS") == list(MCP_KEYS)


def test_the_node_output_built_ins_are_the_python_ones():
    """These are what a repo with NO `.fux/output.toml` gets — every repo that
    predates the file, which is most of them."""
    import json

    from fux.output_config import BUILT_IN

    source = _source("config/output.mjs")
    body = re.search(r"export const BUILT_IN = \{(.*?)\};", source, re.S)
    assert body, "no `BUILT_IN` in config/output.mjs"
    written = dict(
        (k, json.loads(v)) for k, v in re.findall(r"(\w+): (true|false|\d+)", body.group(1))
    )
    assert written == BUILT_IN


# -- the decode boundary -----------------------------------------------------


def test_the_node_prose_types_are_the_python_ones():
    """🔴 The set that decides whether Node may CITE a document at all.

    Node has no decoders, so it refers only documents that are already text and
    skips the rest (ADR-NODE-SEARCH decision 11). A format that is prose on one
    side and not the other is not a cosmetic drift: too wide and Node cites
    line numbers into text the index never held; too narrow and it declines a
    document it could have answered from.
    """
    from fux.ingest.gitdir import _PROSE_TYPES

    source = _source("decode/registry.mjs")
    assert sorted(_js_string_list(source, "export const PROSE_TYPES")) == sorted(_PROSE_TYPES)


def test_the_node_pii_gate_path_is_the_python_one():
    """The third copy of the path, beside `cli.py` and `api.py`.

    `tests/test_cli.py` holds the Python copies equal to each other and to the
    Node literal; this asserts the Node side still spells it, so a refactor
    that drops the gate fails here too rather than only in a file about the CLI.
    """
    from fux.ingest.pii import rules_path

    entry = (ROOT / "node" / "fux.mjs").read_text(encoding="utf-8")
    spelled = re.search(r'const PII_RULES = \[(.*?)\];', entry)
    assert spelled, "node/fux.mjs no longer spells the PII gate path"
    parts = re.findall(r'"([^"]*)"', spelled.group(1))
    assert parts == list(rules_path(Path(".")).parts[-2:])
