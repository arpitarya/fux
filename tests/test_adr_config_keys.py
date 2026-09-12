"""The key-tree gate — a record and its code, held equal in both directions.

**This is the check R-2 asked for and two earlier sessions correctly refused to
write.** It was unwritable while a configuration key crossed four artifacts (the
record, `config.schema.json`, `config.py`, its consumer): any check spanning four
sources of truth is an approximation, and shipping a loose one is the
moving-threshold failure in another costume.
[ADR-LAW-0](../docs/adr/0002_LAW-0-authority.md) collapsed the sources to one, and
**with one source the check is a parser** — decision 6: *a key is real only if it
is in its record's declared block.*

## The two failures this would have caught

- **`acquired_max_bytes`** — named in ADR-ACQUIRED's prose and in the ownership
  table, never parsed by `config.py`, reached through an undefined name by
  `urlsrc.fetch_all`. A `NameError` on every retaining fetch.
- **`[sources] types_file`** — advertised by `config.schema.json` with a default,
  read by nothing, so the key was silently ignored for as long as it existed.

**Both are the same shape from opposite ends**: a key in the documentation that is
not in the code, and a key in the documentation that the code never looks for.
The gate runs both directions for exactly that reason.

## What it does NOT check

⚠ **Nothing here reads what a key *means*.** A record can describe
`max_parallel` as a timeout and this test stays green. Names and sigils are what
is mechanised; semantics stay judgment, as ADR-LAW-0 §"What is gated, and what is
not" says plainly.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import tomllib

from fux import config as config_mod
from fux import tune as tune_mod
from fux.errors import FuxError

ROOT = Path(__file__).resolve().parents[1]
ADR_CONFIG = ROOT / "docs" / "adr" / "0113_config.md"
ADR_TUNE = ROOT / "docs" / "adr" / "0135_tuning.md"

#: The fence the declared block is written in. Deliberately not ```toml or
#: ```text: a dedicated info string means a reader (and this parser) can tell the
#: normative block from the annotated examples around it, which are prose.
_FENCE = "```keys"


def _declared(path: Path) -> dict[str, list[str]]:
    """One record's declared key block, as `{sigil: [entry, …]}`.

    Grammar, and there is no more of it than this: one entry per line, a sigil,
    a space, a dotted path. `#` comments and blank lines are skipped. A fourth
    sigil is a hard failure rather than a guess — a parser that shrugs at an
    unknown marker is how a block stops meaning anything.
    """
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"^```keys\n(.*?)^```", text, flags=re.S | re.M)
    assert len(blocks) == 1, (
        f"{path.name} must carry exactly one {_FENCE} block, found {len(blocks)}"
    )
    out: dict[str, list[str]] = {"+": [], "*": [], "-": []}
    for line in blocks[0].split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sigil, _, entry = line.partition(" ")
        assert sigil in out, f"{path.name}: unknown sigil {sigil!r} in {line!r}"
        assert entry.strip(), f"{path.name}: sigil with no key in {line!r}"
        out[sigil].append(entry.strip())
    return out


# -- ADR-CONFIG <-> config.py -------------------------------------------------


@pytest.fixture(scope="module")
def declared_config() -> dict[str, list[str]]:
    return _declared(ADR_CONFIG)


def test_the_config_block_is_not_empty(declared_config):
    """A parser over an empty block passes vacuously — R6 tier 1's failure."""
    assert len(declared_config["+"]) >= 10
    assert declared_config["*"] and declared_config["-"]


def test_every_declared_config_key_is_parsed(declared_config):
    """Record → code. A key in the block that `config.py` does not know is the
    `acquired_max_bytes` defect: documented, never read."""
    assert sorted(declared_config["+"]) == sorted(config_mod.KNOWN_KEYS)


def test_every_parsed_config_key_is_declared(declared_config):
    """Code → record. A key `config.py` reads that the record does not list is
    undeclared configuration — real behaviour with no decision behind it."""
    assert sorted(config_mod.KNOWN_KEYS) == sorted(declared_config["+"])


def test_the_opaque_tables_agree(declared_config):
    assert sorted(declared_config["*"]) == sorted(config_mod.OPAQUE_TABLES)


def test_the_refused_spellings_agree(declared_config):
    assert sorted(declared_config["-"]) == sorted(config_mod.REFUSED_KEYS)


def test_no_key_carries_two_sigils(declared_config):
    """`+ x` and `- x` together would make the block unreadable and the code's
    behaviour a coin-toss between two rules."""
    seen = [e for entries in declared_config.values() for e in entries]
    assert len(seen) == len(set(seen)), f"duplicate entries: {sorted(seen)}"


# -- the refused keys actually refuse ----------------------------------------


def _write(tmp_path: Path, body: str) -> Path:
    (tmp_path / "fux.toml").write_text(body, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("dotted", config_mod.REFUSED_KEYS)
def test_a_refused_spelling_errors_by_name(tmp_path, dotted):
    """🔴 **The hole this closes.** `_refuse_unknown_keys` SKIPS anything in
    `REFUSED_KEYS`, on the grounds that each one has a better, bespoke error
    naming its new home. If that bespoke check were ever deleted, the skip would
    silently turn a refusal into an acceptance — the key would parse and do
    nothing, which is the exact failure mode the refusal exists to prevent.

    So: every refused spelling is fed to the loader and must raise, and the
    message must name the key.
    """
    parts = dotted.split(".")
    leaf = parts[-1]
    table = ".".join(parts[:-1])
    body = f"[{table}]\n{leaf} = \"x\"\n" if table else f"[{leaf}]\nany = 1\n"
    root = _write(tmp_path, body)
    with pytest.raises(FuxError) as exc:
        config_mod.load(root)
    assert leaf in str(exc.value), f"the error for {dotted} must name it: {exc.value}"


def test_an_undeclared_key_is_refused(tmp_path):
    """ADR-CONFIG decision 14 — the W-140 row 8 defect. A typo used to parse."""
    root = _write(tmp_path, '[sources]\ndirs_fil = "docs"\n')
    with pytest.raises(FuxError, match="dirs_fil is not a fux.toml key"):
        config_mod.load(root)


def test_an_undeclared_table_is_refused(tmp_path):
    root = _write(tmp_path, "[extract]\nmax_rows = 5\n")
    with pytest.raises(FuxError, match="extract is not a fux.toml key"):
        config_mod.load(root)


def test_an_opaque_table_keeps_its_own_vocabulary(tmp_path):
    """`[sources.url.config]` is `*`, so a key inside it is the fetcher's
    business and fux must not have an opinion (ADR-CONFIG decision 8)."""
    root = _write(
        tmp_path,
        "[sources.url]\nmax_parallel = 4\n\n[sources.url.config]\n"
        'cdp_port = 9222\nanything_at_all = "fine"\n',
    )
    assert config_mod.load(root).url.config["anything_at_all"] == "fine"


def test_what_setup_writes_still_loads(tmp_path):
    """The template and the loader are the two halves that must not drift: a
    refused key in fux's own generated `fux.toml` would break every first run."""
    from fux import setup as setup_mod

    setup_mod.run(tmp_path)
    config_mod.load(tmp_path)


def test_this_repos_own_config_loads():
    """Dogfood. fux's `fux.toml` is a real consumer file and the first thing an
    unknown-key refusal would break."""
    config_mod.load(ROOT)


# -- ADR-TUNE <-> tune.py's _SCHEMA ------------------------------------------


@pytest.fixture(scope="module")
def declared_tune() -> dict[str, list[str]]:
    return _declared(ADR_TUNE)


def _tune_entries() -> tuple[list[str], list[str]]:
    """`_SCHEMA` flattened to dotted `+` entries, and the open tables as `*`.

    An open table (`[priority]`) has consumer-chosen keys — its entries cannot be
    enumerated, which is the same property `[sources.url.config]` has, so it takes
    the same sigil rather than a fourth one.
    """
    keys, open_tables = [], []
    for table, fields in tune_mod._SCHEMA.items():
        if table in tune_mod._OPEN_TABLES:
            open_tables.append(table)
            continue
        keys.extend(f"{table}.{field}" for field in fields)
    return sorted(keys), sorted(open_tables)


def test_every_declared_tune_key_is_in_the_schema(declared_tune):
    keys, _ = _tune_entries()
    assert sorted(declared_tune["+"]) == keys


def test_every_tune_schema_key_is_declared(declared_tune):
    keys, _ = _tune_entries()
    assert keys == sorted(declared_tune["+"])


def test_the_tune_open_tables_agree(declared_tune):
    _, open_tables = _tune_entries()
    assert sorted(declared_tune["*"]) == open_tables


def test_the_tune_specimen_only_names_declared_keys(declared_tune):
    """`tune.specimen()` is what `fux setup` writes, and ADR-TUNE already names
    it as the authority for the file's shape. A specimen key outside the schema
    would be a key a consumer copies and the loader then refuses."""
    text = tune_mod.specimen()
    # Uncomment every key line, so the specimen parses as the file it describes.
    live = "\n".join(
        line.lstrip("#") if re.match(r"#\s*[a-z_]+\s*=", line) else line
        for line in text.split("\n")
    )
    data = tomllib.loads(live)
    declared = set(declared_tune["+"])
    open_tables = set(declared_tune["*"])
    for table, body in data.items():
        if table in open_tables:
            continue
        assert isinstance(body, dict), f"[{table}] is not a table in the specimen"
        for key in body:
            assert f"{table}.{key}" in declared, (
                f"tune.specimen() writes [{table}] {key}, which ADR-TUNE does not declare"
            )
