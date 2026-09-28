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

W-107 R5 / SR-NODE-SEARCH decision 8.
"""

from __future__ import annotations

from l12_fixtures import template_tune
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_SRC = ROOT / "node" / "src"


def _source(rel: str) -> str:
    return (NODE_SRC / rel).read_text(encoding="utf-8")


def _node_export(rel: str, name: str):
    """What `node/src/<rel>` exports as `name`, evaluated by Node itself.

    Since L12 (W-225) a shared value is READ from one TOML file by both planes
    rather than spelled twice, so the Node source no longer carries the literal
    a regex could find. The value it actually holds is what parity means.
    """
    url = (NODE_SRC / rel).as_uri()
    script = f"import({json.dumps(url)}).then(m => process.stdout.write(JSON.stringify(m[{json.dumps(name)}])))"
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


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
            # `anchor` (W-168 step 1) is literal on both sides for the same
            # reason it is not in `FIELD_KEYS`: it is not one of the five
            # committed fields, it is the read-time sixth.
            assert spelled == ["k1", "b", "anchor"], "the [bm25f] scalars drifted"
            continue
        assert spelled == list(keys), f"[{table}] key set differs from tune.py"


def _node_tune(root: Path, enabled: bool) -> dict:
    """Node's resolved `Tune` for `root`, as JSON — or `{"error": message}`."""
    url = (NODE_SRC / "config" / "tune.mjs").as_uri()
    script = (
        f"import({json.dumps(url)}).then(m => {{"
        f" try {{ process.stdout.write(JSON.stringify(m.loadTune({json.dumps(str(root))},"
        f" {{ enabled: {'true' if enabled else 'false'} }}))); }}"
        " catch (e) { process.stdout.write(JSON.stringify({ error: e.message })); } })"
    )
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.title() for part in rest)


def test_both_readers_resolve_the_template_to_the_same_tune(tmp_path):
    """Since L12 there is no default to spell twice: both readers read the SAME
    template file, and this checks they read it to the same values, field by
    field — the property the old spelling tests only approximated."""
    import dataclasses

    from fux.tune import load

    py = dataclasses.asdict(load(tmp_path, enabled=False))
    node = _node_tune(tmp_path, enabled=False)
    assert "error" not in node, node
    for field, value in py.items():
        got = node[_camel(field)]
        if isinstance(value, tuple):
            value = [list(v) if isinstance(v, tuple) else v for v in value]
        assert got == value, f"`{field}`: Python {value!r}, Node {got!r}"


def test_both_readers_name_a_missing_key_in_the_same_words(tmp_path):
    """L12 decision 4's other half: the SAME error, not merely an error."""
    from fux.errors import FuxError
    from fux.tune import load, template_text

    path = tmp_path / ".fux" / "tune.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(l for l in template_text().splitlines() if not l.startswith("mined_weight")),
        encoding="utf-8",
    )
    with pytest.raises(FuxError) as exc:
        load(tmp_path, enabled=True)
    node = _node_tune(tmp_path, enabled=True)
    py_lines = str(exc.value).splitlines()[1:]
    node_lines = node["error"].splitlines()[1:]
    assert py_lines == node_lines == [
        "  [ranking] mined_weight is missing",
        "  `fux doctor --fix` writes every missing key from the template `fux setup` uses",
    ]


def test_both_readers_name_a_missing_file_in_the_same_words(tmp_path):
    from fux.errors import FuxError
    from fux.tune import load

    with pytest.raises(FuxError) as exc:
        load(tmp_path, enabled=True)
    node = _node_tune(tmp_path, enabled=True)
    assert node["error"] == str(exc.value).replace(str(tmp_path / ".fux" / "tune.toml"), f"{tmp_path}/.fux/tune.toml")


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


def _node_output(root, enabled: bool) -> dict:
    """Node's resolution of every output key for `root` — `{verb.key: value}`."""
    url = (NODE_SRC / "config" / "output.mjs").as_uri()
    script = (
        f"import({json.dumps(url)}).then(m => {{ const c = m.loadOutput("
        f"{json.dumps(str(root) if root else None)}, {{ enabled: {'true' if enabled else 'false'} }});"
        " const out = { json: c.resolveJson('ask') };"
        " for (const [v, ks] of Object.entries(m.CLI_VERBS)) for (const k of ks) out[`${v}.${k}`] = c.resolve(v, k, undefined, { asJson: false });"
        " for (const k of m.MCP_KEYS) out[`mcp.${k}`] = c.resolveMcp(k);"
        " process.stdout.write(JSON.stringify(out)); })"
    )
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _python_output(root, enabled: bool) -> dict:
    from fux.output_config import CLI_VERBS, MCP_KEYS, load

    c = load(root, enabled=enabled)
    out: dict = {"json": c.resolve_json("ask")}
    for verb, keys in CLI_VERBS.items():
        for key in keys:
            out[f"{verb}.{key}"] = c.resolve(verb, key, as_json=False)
    for key in MCP_KEYS:
        out[f"mcp.{key}"] = c.resolve_mcp(key)
    return out


def test_both_readers_resolve_every_output_key_alike_from_the_template():
    """Since L12 there is no built-in dict to compare: both readers read the
    one template, and this holds that they resolve every key of every verb —
    and `[mcp]` — to the same value."""
    assert _node_output(None, enabled=False) == _python_output(None, enabled=False)


def test_both_readers_resolve_this_repos_own_output_toml_alike():
    root = Path(__file__).resolve().parents[1]
    assert _node_output(root, enabled=True) == _python_output(root, enabled=True)


def test_the_journal_key_is_bound_on_BOTH_runtimes_by_name():
    """🔴 W-147, and it names `journal` rather than trusting the checks above.

    SR-PROVENANCE decision 10 as amended makes a committed
    `[cli.answer] journal = true` explicit consent, and the failure mode the
    ruling guards against is a later session reading `.fux/output.toml` as a
    pure *rendering* config and tidying the key out of one runtime. A test that
    only fails as *"`answer` key set differs"* does not tell that session what it
    just broke; this one does.
    """
    from fux.output_config import CLI_VERBS, template

    assert "journal" in CLI_VERBS["answer"], "the Python side lost the key"
    assert template().resolve("answer", "journal", as_json=False) is False, "journalling must never ship ON"

    source = _source("config/output.mjs")
    assert re.search(r'answer: \[[^\]]*"journal"', source), (
        "`node/src/config/output.mjs` no longer carries `journal` under `answer`. "
        "It is the ONE key in that file that writes a durable file, and a runtime "
        "that drops it silently ignores a consumer's committed consent."
    )


# -- the decode boundary -----------------------------------------------------


def test_the_node_prose_types_are_the_python_ones():
    """🔴 The set that decides whether Node may CITE a document at all.

    Node has no decoders, so it refers only documents that are already text and
    skips the rest (SR-NODE-SEARCH decision 11). A format that is prose on one
    side and not the other is not a cosmetic drift: too wide and Node cites
    line numbers into text the index never held; too narrow and it declines a
    document it could have answered from.
    """
    from fux.ingest.gitdir import _PROSE_TYPES

    assert sorted(_node_export("decode/registry.mjs", "PROSE_TYPES")) == sorted(_PROSE_TYPES)


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


def test_the_dirs_attribute_set_is_the_python_one():
    """🔴 **The gap `test_node_twins`'s narrowing leaves open, closed by parity.**

    `node/src/ingest/sourcelist.mjs` mirrors the **`dirs` half** of
    `src/fux/ingest/sourcelist.py` — Node never fetches, so the `urls` spec
    decides nothing there. The freshness check therefore narrows that twin to
    `parse`, the shared grammar engine; a change to the `dirs` **attribute
    tuple** lives at module level, outside any `def`, and git's hunk-context
    header cannot name it.

    So the tuple is held by its VALUE rather than by whether anyone edited the
    file, which is the better check of the two: `query/__init__.py` catches a
    refusal from this parser and degrades to *no archived directories*, so a
    Node reader with a different attribute set returns a **different archived
    set from the same committed file** — the loud half and the lenient half
    disagreeing, which is worse than either alone.
    """
    from fux.ingest.sourcelist import DIRS

    source = _source("ingest/sourcelist.mjs")
    body = re.search(r"const DIRS_ATTRIBUTES = \[(.*?)\n\];", source, re.S)
    assert body, "no `DIRS_ATTRIBUTES` in ingest/sourcelist.mjs"

    rows = re.findall(
        r'\[\s*"([a-z_]+)"\s*,\s*\[([^\]]*)\]\s*,\s*"([a-z]+)"', body.group(1)
    )
    node = [
        (name, tuple(v.strip().strip('"') for v in vals.split(",")), default)
        for name, vals, default in rows
    ]
    python = [(a.name, a.values, a.default) for a in DIRS.attributes]
    assert node == python, (
        "the two readers disagree about `.fux/sources/dirs`:\n"
        f"  node:   {node}\n  python: {python}"
    )
