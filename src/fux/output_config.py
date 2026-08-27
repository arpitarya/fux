"""`.fux/output.toml` — every knob that changes HOW a result is SHOWN.

[ADR-OUTPUT](../../docs/adr/0047_output-defaults.md) is the record. What this module is:

- **The loader.** Absent, empty, or every key commented out means every
  default — no error, no warning, no file required. `$0` stays `$0`.
- **The validator.** The key set is **closed** per verb: an unknown table or
  key is a loud error, for the same reason `tune.py` closes its own — a typo
  in a file that changes every invocation must not fail silently.
- **The resolver.** `resolve(verb, key, cli_value)` applies one precedence
  chain and nothing else: **an explicit CLI flag wins, then `[<verb>]`, then
  `[defaults]`, then the engine's built-in.**

## The boundary rule, which is mechanical rather than a taste

A value belongs here if and only if changing it leaves **the ranked result set
and its order identical**. This file may change what is *emitted*; it may never
change what is *computed*.

⚠ **That rule said "printed" until 2026-08-27, and `journal` widened it.**
Arpit ruled the query journal's persistent switch into this file rather than
`tune.toml`, and **writing a file is not printing** — so the rule as written
would have excluded the very key it was being asked to hold. **Widening it in
the open beats letting one key quietly not fit**: the boundary that matters is
*emission vs computation*, and journalling is emission to a different sink.

⚠ **The honest cost of the wider word.** *"Emitted"* admits more than
*"printed"* did, and the next key that writes somewhere will cite `journal` as
precedent. The fence that remains is decision 2's second half — **it may never
change what is computed** — plus the L3 import fence below, and those are what
a reviewer should check, not the verb.

**That is a different boundary from `.fux/tune.toml`, and the difference is the
whole reason this is a second file.** `tune.toml`'s rule is *"leaves
`.fux/index/` byte-identical"* — which output defaults also satisfy, so
tune.toml's rule alone would have admitted them. The distinguishing question is
one step further in:

| file | the mechanical test |
|---|---|
| `fux.toml` | does it change **what is indexed**? |
| `.fux/tune.toml` | does it change **which documents come back, or in what order**? |
| `.fux/output.toml` | neither — it changes **how they are shown** |

⚠ **`top` is the honest boundary case, and it is admitted rather than hidden.**
It truncates a ranking; it does not reorder one, so the rule holds. But
`confidence.support` is bounded by `top`
([ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) §Consequences), so
**changing `top` changes a reported signal**. That coupling is stated here and
in the shipped specimen rather than discovered later.

**Nothing here is read on the maintenance path.** Not by `ingest`, not by
`build`, not by the hooks — L3 says no maintenance output may depend on
anything but the sources, and a rendering preference is not a source.
`tests/test_output_config.py` asserts the import fence over this module's
own import block.

## Why a committed file and not just flags

An **MCP tool call has no flags at all**, so before this file `fux_search`'s
output shape was unconfigurable in principle rather than merely inconvenient.
And [ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) decision 11 accepted a
cost it could only mitigate with documentation — *an agent running a bare
`fux ask` gets no confidence block* — where **documentation is weaker than a
default.** A committed `band = true` is that default, and unlike argv it is
visible in a diff.

## There is no writer, deliberately

`tomllib` reads; nothing in the stdlib writes TOML. `fux output` **prints** a
specimen and the human pastes it — the same refusal `tune.py` makes, for the
same reason (fux never rewrites a file it told you was yours).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import FuxError

__all__ = [
    "OUTPUT_NAME",
    "OutputDefaults",
    "DEFAULT_OUTPUT",
    "BUILT_IN",
    "SCHEMA",
    "load",
    "specimen",
]

#: Committed, and written once by `fux setup`, exactly as `tune.toml` is.
OUTPUT_NAME = ".fux/output.toml"

#: At most this many semantic errors are reported together — `tune.py`'s
#: reasoning, unchanged: one at a time turns a hand-edited file into a guessing
#: game, and an unbounded list buries the first one.
_MAX_REPORTED = 10

#: The table every verb inherits from. A key here reaches a verb **only if that
#: verb declares it** in `SCHEMA` — so `[defaults] band = true` does not put a
#: band on `doctor`, which has no such concept.
DEFAULTS_TABLE = "defaults"

#: The closed key set, verb -> keys. **Adding a key here is a change to the
#: record, not a convenience.**
#:
#: Read the columns as *"which verb has this knob on its own command line"*.
#: `[mcp]` has no `json` because an MCP result is always JSON, and no `explain`
#: because the tool surface has none.
SCHEMA: dict[str, tuple[str, ...]] = {
    "ask": ("json", "band", "top", "explain"),
    "find": ("json", "band", "top"),
    "answer": ("json", "band", "no_refer", "journal"),
    "explain": ("json",),
    "graph": ("json", "top"),
    "path": ("json", "hops"),
    "doctor": ("json",),
    "hooks": ("json",),
    "daemon": ("json",),
    # The one surface with no flags. This table is its ONLY knob.
    #
    # ⚠ **`top` only — NOT `band`.** The first draft of this record carried
    # `band` here and it was wrong: ADR-CONFIDENCE decision 11 makes the MCP
    # result's confidence block **unconditional**, precisely because a tool
    # call cannot pass a flag. A `[mcp] band = false` would re-blind the one
    # surface this whole file exists to serve, so it is refused by name below
    # rather than quietly honoured.
    "mcp": ("top",),
}

#: Every key `[defaults]` may carry: the union of keys that appear on more than
#: one verb. A key unique to one verb (`explain`, `no_refer`, `hops`) is
#: refused in `[defaults]` **by name**, because setting it there reads as
#: global and is not.
_SHARED_KEYS = ("json", "band", "top")

#: The engine's own defaults, per key. **This is the single source** — the CLI
#: reads them from here rather than repeating them in `add_argument`, so
#: `--top`'s help text and this table cannot drift apart.
BUILT_IN: dict[str, object] = {
    "json": False,
    "band": False,
    "top": 5,
    "explain": False,
    "no_refer": False,
    "hops": 2,
    "journal": False,
}

#: Type per key, for validation. `bool` is checked before `int` everywhere,
#: because in Python `True` is an `int` and a silently-accepted `top = true`
#: would truncate every result list to one.
_TYPES: dict[str, type] = {
    "json": bool,
    "band": bool,
    "explain": bool,
    "no_refer": bool,
    "journal": bool,
    "top": int,
    "hops": int,
}

#: Keys refused **by name, with the reason**, rather than reported as unknown.
#: Each is something a reader will plausibly try; a bare *"unknown key"* would
#: send them hunting for a typo in a word they spelled correctly.
#:
#: The rule these follow is Arpit's standing one: **refuse only what is broken
#: or duplicates a tool that already exists; state the cost of anything that is
#: merely strong.** None of these is a preference being denied.
_REFUSED: dict[str, str] = {
    "no_tune": (
        "`--no-tune` is the *'is it me or the config?'* switch. A config file "
        "that can turn off config-reading defeats the one flag whose entire "
        "job is to answer that question"
    ),
    "tune": (
        "`--no-tune` is the *'is it me or the config?'* switch. A config file "
        "that can turn off config-reading defeats the one flag whose entire "
        "job is to answer that question"
    ),
    "no_output_config": (
        "the same loop one level up — this file may not decide whether this "
        "file is read. Pass `--no-output-config` on the command line"
    ),
    "fast": (
        "`--fast` and `--scan` choose a candidate path, not an output shape, "
        "and the two are asserted byte-identical — so this is not an output "
        "key. `--scan` exists so a bug report can be reproduced explicitly, "
        "which a configured default would silently defeat"
    ),
    "scan": (
        "`--fast` and `--scan` choose a candidate path, not an output shape, "
        "and the two are asserted byte-identical — so this is not an output "
        "key. `--scan` exists so a bug report can be reproduced explicitly, "
        "which a configured default would silently defeat"
    ),
    "no_progress": (
        "progress is stderr-only and already TTY-gated, so it is off wherever "
        "output is being consumed. A configured default here would fight the "
        "TTY detection rather than replace it. Use `--no-progress`"
    ),
}


@dataclass(frozen=True)
class OutputDefaults:
    """Resolved output defaults. Construct via `load()`.

    Frozen, like `Tune` and `Confidence`, so a caller can never hand two code
    paths a block that drifted between them.
    """

    #: `verb -> {key: value}`, carrying only what the file actually set.
    #: **Absent means not set**, never *"set to the default"* — the distinction
    #: is what lets `resolve()` fall through cleanly.
    per_verb: dict[str, dict[str, object]]
    #: `[defaults]`, likewise carrying only what was set.
    shared: dict[str, object]

    @property
    def trivial(self) -> bool:
        """True when nothing was set — used to skip work, never to skip a check."""
        return not self.per_verb and not self.shared

    def resolve(self, verb: str, key: str, cli_value: object = None) -> object:
        """One precedence chain: **flag → `[verb]` → `[defaults]` → built-in.**

        `cli_value` is `None` for *"the flag was not passed"*. A `store_true`
        flag therefore has to be declared `default=None` on its parser, or
        `False` would be indistinguishable from absent and the file could never
        take effect — that is the one CLI change this module requires, and it
        is the whole of it.

        Raises on a verb/key pair `SCHEMA` does not grant, so a typo in a
        CALLER is caught too, not only a typo in the file.
        """
        allowed = SCHEMA.get(verb)
        if allowed is None:
            raise FuxError(f"no output defaults are declared for `{verb}` — known: {sorted(SCHEMA)}")
        if key not in allowed:
            raise FuxError(f"`{key}` is not an output key for `{verb}` — it has: {sorted(allowed)}")
        if cli_value is not None:
            return cli_value
        table = self.per_verb.get(verb, {})
        if key in table:
            return table[key]
        # `[defaults]` reaches a verb only where the verb declares the key,
        # which is already true here: `key in allowed` was checked above.
        if key in self.shared:
            return self.shared[key]
        return BUILT_IN[key]


DEFAULT_OUTPUT = OutputDefaults(per_verb={}, shared={})


class _Collector:
    """Gathers semantic errors so a hand-edited file reports them together."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.errors: list[str] = []

    def add(self, message: str) -> None:
        self.errors.append(message)

    def raise_if_any(self) -> None:
        if not self.errors:
            return
        shown = self.errors[:_MAX_REPORTED]
        more = len(self.errors) - len(shown)
        tail = f"\n  ... and {more} more" if more > 0 else ""
        raise FuxError(f"{self.path}:\n  " + "\n  ".join(shown) + tail)


def _reject_conflict_markers(path: Path, text: str) -> None:
    """A merged-but-unresolved file is a parse error with a useless message.

    Same guard `tune.py` carries, for the same reason: this file is committed,
    so it can arrive conflicted from a pull.
    """
    for marker in ("<<<<<<<", "=======", ">>>>>>>"):
        if any(line.startswith(marker) for line in text.splitlines()):
            raise FuxError(
                f"{path}: unresolved merge conflict markers — resolve the conflict before fux reads it"
            )


def _checked(c: _Collector, table: str, key: str, value: object) -> object | None:
    """Validate one key/value. Returns `None` when it was rejected."""
    if key in _REFUSED:
        c.add(f"[{table}] `{key}` is refused: {_REFUSED[key]}")
        return None
    want = _TYPES[key]
    if want is bool:
        if not isinstance(value, bool):
            c.add(f"[{table}] {key} must be true or false (got {value!r})")
            return None
        return value
    # bool BEFORE int, always: `isinstance(True, int)` is True in Python, so
    # the obvious check would accept `top = true` and silently mean `top = 1`.
    if isinstance(value, bool) or not isinstance(value, int):
        c.add(f"[{table}] {key} must be a whole number (got {value!r})")
        return None
    if value < 1:
        c.add(
            f"[{table}] {key} must be at least 1 — at zero the verb returns nothing, "
            f"which is a broken setting rather than an aggressive one (got {value})"
        )
        return None
    return value


def load(root: Path, *, enabled: bool = True) -> OutputDefaults:
    """Read `.fux/output.toml`. Absent, empty or all-commented means every default.

    `enabled=False` is `--no-output-config`: the file is not read at all, so
    what you see is the engine's own shape. Mirrors `tune.load`'s `enabled`
    for the same *"is it me or the config?"* reason.
    """
    if not enabled:
        return DEFAULT_OUTPUT

    path = root / OUTPUT_NAME
    if not path.is_file():
        return DEFAULT_OUTPUT

    # Windows editors write a BOM; `tomllib.load` reads binary and fails with a
    # decode error that names nothing useful. Windows-first fleets are in the
    # litmus, so this is stripped rather than diagnosed.
    text = path.read_bytes().decode("utf-8-sig")
    _reject_conflict_markers(path, text)

    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc

    if not data:
        return DEFAULT_OUTPUT

    known = set(SCHEMA) | {DEFAULTS_TABLE}

    # A bare `band = true` at the top of the file parses as a top-level KEY,
    # not as a table, so the unknown-table check below would report it as an
    # unknown *table* named `band` — which sends a reader looking for a
    # section they never wrote. Name what they actually did instead.
    stray = [k for k, v in data.items() if k not in known and not isinstance(v, dict)]
    if stray:
        first = stray[0]
        if first in BUILT_IN:
            owners = sorted(v for v, keys in SCHEMA.items() if first in keys)
            raise FuxError(
                f"{path}: `{first}` is a key, not a table — every key lives inside a "
                f"section. Put it in [{owners[0]}]"
                + (f" (or [{DEFAULTS_TABLE}])" if first in _SHARED_KEYS else "")
            )
        raise FuxError(
            f"{path}: `{first}` is a bare key at the top of the file — every key lives "
            f"inside a section, and `{first}` is not a known key at all"
        )

    unknown_tables = [k for k in data if k not in known]
    if unknown_tables:
        raise FuxError(
            f"{path}: unknown table(s) {sorted(unknown_tables)} — known: {sorted(known)}. "
            "The key set is closed on purpose: this file changes the shape of every "
            "invocation without changing a byte of the index, so a typo here must not "
            "fail silently"
        )

    c = _Collector(path)
    shared: dict[str, object] = {}
    per_verb: dict[str, dict[str, object]] = {}

    for name, value in data.items():
        if not isinstance(value, dict):
            raise FuxError(
                f"{path}: `{name}` must be a table (a `[{name}]` section), not a bare key"
            )
        if name == DEFAULTS_TABLE:
            for key, raw in value.items():
                if key in _REFUSED:
                    c.add(f"[{name}] `{key}` is refused: {_REFUSED[key]}")
                    continue
                if key not in _SHARED_KEYS:
                    if key in BUILT_IN:
                        owners = sorted(v for v, keys in SCHEMA.items() if key in keys)
                        c.add(
                            f"[{name}] `{key}` belongs to one verb only ({', '.join(owners)}) — "
                            f"setting it here reads as global and is not. Put it in [{owners[0]}]"
                        )
                    else:
                        c.add(
                            f"[{name}] unknown key `{key}` — [{DEFAULTS_TABLE}] carries "
                            f"{sorted(_SHARED_KEYS)}"
                        )
                    continue
                checked = _checked(c, name, key, raw)
                if checked is not None:
                    shared[key] = checked
            continue

        allowed = SCHEMA[name]
        table: dict[str, object] = {}
        for key, raw in value.items():
            if name == "mcp" and key == "band":
                c.add(
                    "[mcp] `band` is refused: the MCP result's confidence block is "
                    "UNCONDITIONAL (ADR-CONFIDENCE decision 11) because a tool call "
                    "has no flags to pass. Turning it off here would re-blind the one "
                    "surface these defaults exist to serve. Use [ask] / [find] / "
                    "[answer] to gate the CLI"
                )
                continue
            if key in _REFUSED:
                c.add(f"[{name}] `{key}` is refused: {_REFUSED[key]}")
                continue
            if key not in allowed:
                hint = ""
                if key in BUILT_IN:
                    owners = sorted(v for v, keys in SCHEMA.items() if key in keys)
                    hint = f" — it is a key of {', '.join(owners)}, not of `{name}`"
                c.add(f"[{name}] unknown key `{key}`{hint}. [{name}] carries {sorted(allowed)}")
                continue
            checked = _checked(c, name, key, raw)
            if checked is not None:
                table[key] = checked
        if table:
            per_verb[name] = table

    c.raise_if_any()
    return OutputDefaults(per_verb=per_verb, shared=shared)


def specimen() -> str:
    """What `fux output` prints for a human to paste. Every key commented out.

    Commented-out is not decoration: an uncommented specimen would make every
    engine default a *committed* value, so a later change to a default could
    never reach anyone who had run `fux setup`.
    """
    return """\
# .fux/output.toml — HOW a result is SHOWN. Never which documents come back.
#
# Written once by `fux setup`; fux never rewrites it. Absent, empty, or every
# key commented out means every default — this file is optional.
#
# The rule for what may live here is mechanical: changing any value below
# leaves the ranked result set AND ITS ORDER identical. It changes what is
# printed, never what is computed. (`.fux/tune.toml` is the file that changes
# ordering; `fux.toml` is the file that changes what is indexed.)
#
# Precedence, highest first:  a CLI flag  →  [<verb>]  →  [defaults]  →  built-in.
#
# `fux ask --no-output-config` ignores this file entirely, which is the
# "is it me or the config?" switch.

[defaults]           # only keys that more than one verb has
#json = false
#band = false        # the confidence block — ADR-CONFIDENCE decision 11
#top  = 5            # ⚠ also bounds `confidence.support`, which is a REPORTED
                     #   signal. This is the one key here that changes a number
                     #   an agent reads, and it is admitted rather than hidden.

[ask]
#top     = 5
#band    = true      # recommended when an agent consumes this repo: a bare
                     # `fux ask` is otherwise blind to `answerable: false`
#explain = false

[find]
#top  = 5
#band = false        # `find` pipes bare paths; a band on stdout would break that

[answer]
#band     = false
#no_refer = false
#journal  = false    # record each answer's receipt to the local, gitignored
                     # journal. ⚠ OFF by default and that is deliberate: a $0
                     # offline tool may not quietly begin recording questions
                     # because a config line exists somewhere. `--journal` is
                     # still the per-run switch.

[graph]
#top = 5

[path]
#hops = 2

[explain]
#json = false

[doctor]
#json = false

[hooks]
#json = false

[daemon]
#json = false

[mcp]                # the one surface with NO command-line flags at all.
                     # This table is the only way to configure it.
                     # ⚠ There is deliberately no `band` key: the MCP result's
                     # confidence block is UNCONDITIONAL, because a tool call
                     # cannot pass a flag. Setting it here is refused.
#top = 5
"""
