"""The config files every hand-built test repo now needs — L12 (W-225).

[SR-LAW-12](../records/0013_LAW-12-values-live-in-config.md): the engine holds
no value in code, so a repository with no `.fux/tune.toml` stops the ranked
verbs and `fux ingest` naming the file. A test that hand-builds a repository
writes the files `fux setup` would, from the same packaged templates, through
this module — never from literals of its own, so a shipped value changes in one
place (the template) and the suite follows it.

`template_tune()` is the resolved `Tune` a fresh `fux setup` gives: what
`--no-tune` reads, and what a test that needs "the shipped scoring" compares
against.
"""

from __future__ import annotations

import dataclasses
from functools import lru_cache
from pathlib import Path

from fux import tune as tune_mod


@lru_cache(maxsize=1)
def template_tune() -> "tune_mod.Tune":
    """The template's `Tune` — `--no-tune`'s, and a fresh `fux setup`'s."""
    return tune_mod.load(Path("/nonexistent-l12-fixture"), enabled=False)


def tuned(**changes) -> "tune_mod.Tune":
    """The template's `Tune` with some fields replaced."""
    return dataclasses.replace(template_tune(), **changes)


def scoring():
    """The template's BM25F `Scoring`."""
    return template_tune().scoring


def chunk_bounds() -> dict[str, int]:
    """The template's `[refer]` passage bounds, as `chunk` takes them."""
    return template_tune().chunk_bounds()


def write_tune(root: Path, text: "str | None" = None) -> Path:
    """Write `.fux/tune.toml` — the template verbatim, or `text` when given."""
    path = root / ".fux" / "tune.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tune_mod.template_text() if text is None else text, encoding="utf-8")
    return path


def tune_text(**overrides: "dict[str, object]") -> str:
    """The template with some keys changed: `tune_text(bm25f={"k1": 0.9})`.

    Rewrites the one `key = value` line in the named table, so the result is
    still every key the loader requires — a test of one knob never has to spell
    the other forty.
    """
    lines = tune_mod.template_text().split("\n")
    table = None
    pending = {t: dict(v) for t, v in overrides.items()}
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and "]" in stripped and not stripped.startswith("#"):
            table = stripped[1 : stripped.index("]")]
        elif table in pending and "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            if key in pending[table]:
                line = f"{key} = {_toml(pending[table].pop(key))}"
        out.append(line)
    leftover = {t: v for t, v in pending.items() if v}
    for t, keys in leftover.items():
        # A table the template does not carry (e.g. `[priority]` entries).
        out.append(f"[{t}]" if f"[{t}]" not in lines else "")
        out += [f"{_key(k)} = {_toml(v)}" for k, v in keys.items()]
    return "\n".join(out) + "\n"


def _key(key: str) -> str:
    return key if key.replace("_", "").isalnum() else f'"{key}"'


def _toml(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    return repr(value)


@lru_cache(maxsize=1)
def template_index() -> "tune_mod.IndexLimits":
    """The template's `[index]` — what `fux ingest` reads in a fresh repo."""
    import tomllib

    data = tomllib.loads(tune_mod.template_text())["index"]
    return tune_mod.IndexLimits(
        max_phrases=data["max_phrases"], max_table_rows=data["max_table_rows"]
    )


def write_config(root: Path) -> "list[str]":
    """Give a hand-built repo every config key L12 requires, as `fux setup` would.

    Runs the engine's own writer (`setup.fill_missing`, which `fux doctor --fix`
    uses too): a file the test wrote keeps every line it wrote, and gains only
    the keys it lacks, from the packaged templates.
    """
    from fux import setup as setup_mod

    return setup_mod.fill_missing(root)


@lru_cache(maxsize=1)
def configured_root() -> Path:
    """A repository root with every config file and nothing else.

    For a test that calls the engine below the command layer with no corpus of
    its own — a decoder, say — and needs a root to read `[index]` from: the
    engine no longer supplies a cap when nobody names a repository.
    """
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="fux-l12-root-"))
    write_config(root)
    return root
