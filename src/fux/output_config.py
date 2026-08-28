"""`.fux/output.toml` — output defaults, in three roots, one per consumer.

**The boundary, unchanged from the first build of this record.** A key
belongs here iff changing it leaves the ranked result set *and its order*
identical — it may change what is printed, never what is computed. `fux.toml`
asks *what is indexed*; `.fux/tune.toml` asks *which documents come back, or
their order*; this file asks *how are they shown*. `top` is the one admitted
boundary case: it truncates a ranking (allowed) and it bounds
`confidence.support`, a REPORTED signal (stated, not hidden).

## Three roots, because there are three consumers (ADR-OUTPUT decision 3)

| root | consumer | shapes |
|---|---|---|
| `[cli]` | a **person** | stdout text and the stderr notes |
| `[cli.json]` | a **machine reading the CLI** | the `--json` payload |
| `[mcp]` | an **agent** | `fux_search`'s result and its tool schema |

`[mcp]` inherits NOTHING from `[cli]` — a line written for a terminal must
never silently retune the MCP server's default `k`. `[cli.json]` DOES inherit
from `[cli]`, because it is the same command in a different rendering; it
overrides only what should genuinely differ between a human reading and a
machine parsing. Each root may carry a per-verb subtable — `[cli.ask]`,
`[cli.json.ask]` — for an override narrower than "every verb that has this
key".

**`json` is spelled `enabled` and lives only under `[cli.json]`.** TOML
cannot hold both a scalar key `json` and the table `[cli.json]` under `[cli]`
at once, and *"emit the machine form by default"* is a fact about the JSON
rendering anyway, not a CLI key. `enabled` is resolved FIRST, in its own pass
(`resolve_json`), because it selects which chain every other key walks.

**Precedence, highest first:**

```text
  flag passed?           --yes--> value used
        |no
  [cli.json.<verb>] set? --yes--> value used     |  only when
        |no                                      |  the json branch
  [cli.json] set?        --yes--> value used      |  is on
        |no
  [cli.<verb>] set?      --yes--> value used
        |no
  [cli] set?             --yes--> value used
        |no
  bypass? (--no-output-config, or no repo) --yes--> BUILT_IN
        |no
      FuxError -- the file exists but does not set this key
```

## The file is the sole source of truth (Arpit, 2026-08-28)

**Every earlier draft of this record let an unset key fall through to
`BUILT_IN` silently** — "the file is optional, absent means every default".
That is no longer true. **If `.fux/output.toml` is in effect (no
`--no-output-config`, and a repo root exists) and does not set a key a verb
needs, resolving it is a hard `FuxError`** naming the key and where to add
it, not a silent default. `fux setup` (and `fux output`) write every key
**live** — decision 14 — so a repo that has run setup once never sees this;
a repo that has not, or whose `.fux/output.toml` predates a key this version
added, gets a loud, actionable error instead of a value nobody chose and
nobody can see in a diff. This is the "loader refusal" decision 14 named as
the sanctioned remedy for the old design's freeze-at-setup cost, chosen over
the alternative (a silent `fux doctor` warning) because a rendering default
silently drifting from what the repo's own file states is worse than a verb
that refuses to guess.

**`BUILT_IN` still exists** — it is not gone, its JOB changed. It is:
(1) the values `fux setup`/`fux output` write into a fresh, live specimen,
(2) what `--no-output-config` resolves to (the escape hatch has to have
something to fall back to, or it stops being an escape hatch), and (3) what a
run outside any fux repo resolves to, so `--help`/`--version` are never
broken by a file that cannot exist yet. None of the three is "the file was
silently incomplete and nobody noticed".

## There is no writer, deliberately

`tomllib` reads; nothing in the stdlib writes TOML. `fux output` **prints** a
specimen and the human pastes it, or `fux setup` writes it once
(write-if-missing) — the same refusal `tune.py` makes, for the same reason
(fux never rewrites a file it told you was yours).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import FuxError

__all__ = [
    "OUTPUT_NAME",
    "OutputDefaults",
    "DEFAULT_OUTPUT",
    "BUILT_IN",
    "CLI_VERBS",
    "MCP_KEYS",
    "load",
    "specimen",
]

#: Committed, and written once by `fux setup`, exactly as `tune.toml` is.
OUTPUT_NAME = ".fux/output.toml"

#: At most this many semantic errors are reported together.
_MAX_REPORTED = 10

#: The two top-level roots. Anything else at the top of the file is unknown.
_ROOTS = ("cli", "mcp")

#: The closed key set for the `[cli]` / `[cli.json]` roots, per verb. A key
#: here reaches a verb through `[cli.<verb>]` / `[cli.json.<verb>]`, or
#: through the shared `[cli]` / `[cli.json]` table if the verb declares it.
#:
#: ⚠ **`graph` has no `top` key.** It had a dead one on the first build:
#: `graph` has no `--top` flag and reads `seed_depth`/`expand_limit` from
#: `.fux/tune.toml` instead — truncating a graph walk is a ranking change,
#: which this file may not make (ADR-OUTPUT decision 18).
#:
#: `json` is deliberately absent from every tuple below: it is not a `[cli]`
#: key at all, it is the question of WHICH chain the other keys walk
#: (`resolve_json`), answered once per call before any of these are touched.
CLI_VERBS: dict[str, tuple[str, ...]] = {
    "ask": ("band", "top", "explain"),
    "find": ("band", "top"),
    "answer": ("band", "no_refer", "journal"),
    "explain": (),
    "graph": (),
    "path": ("hops",),
    "doctor": (),
    "hooks": (),
    "daemon": (),
}

#: `[mcp]`'s closed key set. `top` only — decision 11. No `json` (an MCP
#: result is always JSON) and, corrected during the first build, no `band`
#: (ADR-CONFIDENCE decision 11 makes the confidence block unconditional over
#: MCP precisely because a tool call cannot pass a flag).
MCP_KEYS: tuple[str, ...] = ("top",)


#: Every key `[cli]` / `[cli.json]` may carry at the shared (non-per-verb)
#: level: keys that more than one verb declares. A key unique to one verb
#: (`explain`, `no_refer`, `journal`, `hops`) is refused at the shared level
#: **by name** — setting it there reads as global and is not — and belongs
#: under that verb's own subtable instead (`[cli.ask]`, `[cli.path]`, ...).
def _keys_shared_by_more_than_one_verb() -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for keys in CLI_VERBS.values():
        for k in keys:
            counts[k] = counts.get(k, 0) + 1
    return tuple(sorted(k for k, n in counts.items() if n > 1))


_SHARED_CLI_KEYS: tuple[str, ...] = _keys_shared_by_more_than_one_verb()

#: The engine's own defaults, per key, as they appear ON `args` / in help
#: text. `json` here is the CLI's `--json`/`enabled` switch's built-in value
#: — see the module docstring for what this dict is used for now that the
#: file itself no longer falls through to it silently.
BUILT_IN: dict[str, object] = {
    "json": False,
    "band": False,
    "top": 5,
    "explain": False,
    "no_refer": False,
    "hops": 2,
    "journal": False,
}

#: Type per key, as spelled IN THE FILE (`enabled`, not `json`). `bool` is
#: checked before `int` everywhere: `isinstance(True, int)` is `True` in
#: Python, so an unguarded check accepts `top = true` and silently means
#: `top = 1`.
_TYPES: dict[str, type] = {
    "band": bool,
    "explain": bool,
    "no_refer": bool,
    "journal": bool,
    "enabled": bool,
    "top": int,
    "hops": int,
}

#: Keys refused **by name, with the reason**, under `[cli]` / `[cli.json]`
#: (at any nesting), rather than reported as unknown.
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
    "json": (
        "`json` is spelled `enabled` and lives only under `[cli.json]` — TOML "
        "cannot hold both a scalar `json` key and the table `[cli.json]` "
        "under `[cli]`, and `enabled` is the fact this file actually states: "
        "whether the JSON rendering is what a bare invocation gets"
    ),
}

#: Keys refused **by name, with the reason**, specifically under `[mcp]`.
#: Separate from `_REFUSED` because `band` is a perfectly valid `[cli]` key —
#: it is only under `[mcp]` that setting it would undo another record's
#: decision.
_MCP_REFUSED: dict[str, str] = {
    "band": (
        "the confidence block is UNCONDITIONAL over MCP (ADR-CONFIDENCE "
        "decision 11) — a tool call cannot pass a flag, so `[mcp] band` "
        "would re-blind the one surface this file exists to serve"
    ),
    "json": "an MCP result is always JSON — there is no rendering to switch",
}


@dataclass(frozen=True)
class OutputDefaults:
    """Resolved output defaults. Construct via `load()`.

    Frozen, like `Tune` and `Confidence`, so a caller can never hand two code
    paths a block that drifted between them.
    """

    #: `[cli]`'s shared scalars.
    cli_shared: dict[str, object] = field(default_factory=dict)
    #: `verb -> {key: value}` from `[cli.<verb>]`.
    cli_verb: dict[str, dict[str, object]] = field(default_factory=dict)
    #: `[cli.json]`'s shared scalars, including `enabled`.
    json_shared: dict[str, object] = field(default_factory=dict)
    #: `verb -> {key: value}` from `[cli.json.<verb>]`.
    json_verb: dict[str, dict[str, object]] = field(default_factory=dict)
    #: `[mcp]`'s scalars.
    mcp: dict[str, object] = field(default_factory=dict)
    #: True for the disabled / no-repo sentinel: every key resolves straight
    #: to `BUILT_IN`, and nothing ever raises for being unset. **Not** "the
    #: file was empty" — an empty *but in-effect* file still raises, because
    #: it is in effect and does not set the key asked for.
    bypass: bool = False

    @property
    def trivial(self) -> bool:
        """True in bypass mode. Kept for callers that want to skip work."""
        return self.bypass

    def resolve_json(self, verb: str, cli_value: object = None) -> bool:
        """Resolve the JSON-rendering switch — FIRST, before any other key.

        `json` selects which chain every other key walks, so it cannot be
        resolved alongside them: `[cli.json] top` would otherwise be
        reachable only when `--json` was typed on the command line and
        unreachable when the file itself turned JSON on, which is the case
        the table exists for.
        """
        if verb not in CLI_VERBS:
            raise FuxError(f"no output defaults are declared for `{verb}` — known: {sorted(CLI_VERBS)}")
        if cli_value is not None:
            return bool(cli_value)
        if self.bypass:
            return bool(BUILT_IN["json"])
        per_verb = self.json_verb.get(verb, {})
        if "enabled" in per_verb:
            return bool(per_verb["enabled"])
        if "enabled" in self.json_shared:
            return bool(self.json_shared["enabled"])
        raise FuxError(
            f"{OUTPUT_NAME} does not set `enabled` for the JSON rendering — "
            f"add `enabled = {bool(BUILT_IN['json'])!s}` under `[cli.json]` "
            f"(or `[cli.json.{verb}]` for `{verb}` only). Run `fux output` to "
            "see every key, or pass --no-output-config to bypass this file."
        )

    def resolve(self, verb: str, key: str, cli_value: object = None, *, as_json: bool = False) -> object:
        """One precedence chain: **flag → json-verb → json-shared →
        cli-verb → cli-shared → bypass → error.**

        Raises on a verb/key pair `CLI_VERBS` does not grant, so a typo in a
        CALLER is caught too, not only a typo in the file. Raises when the
        file is in effect and simply never set this key — see the module
        docstring.
        """
        allowed = CLI_VERBS.get(verb)
        if allowed is None:
            raise FuxError(f"no output defaults are declared for `{verb}` — known: {sorted(CLI_VERBS)}")
        if key not in allowed:
            raise FuxError(f"`{key}` is not an output key for `{verb}` — it has: {sorted(allowed)}")
        if cli_value is not None:
            return cli_value
        if self.bypass:
            return BUILT_IN[key]
        if as_json:
            per_verb = self.json_verb.get(verb, {})
            if key in per_verb:
                return per_verb[key]
            if key in self.json_shared:
                return self.json_shared[key]
        per_verb = self.cli_verb.get(verb, {})
        if key in per_verb:
            return per_verb[key]
        if key in self.cli_shared:
            return self.cli_shared[key]
        where = (
            f"[cli.json.{verb}], [cli.json], [cli.{verb}] or [cli]"
            if as_json
            else f"[cli.{verb}] or [cli]"
        )
        raise FuxError(
            f"{OUTPUT_NAME} does not set `{key}` for `{verb}` — add it under "
            f"{where} (e.g. `{key} = {BUILT_IN[key]!r}`). Run `fux output` to "
            "see every key, or pass --no-output-config to bypass this file."
        )

    def resolve_mcp(self, key: str, tool_value: object = None) -> object:
        """`[mcp]`'s own chain: **tool arg → `[mcp]` → bypass → error.**

        `[mcp]` inherits nothing from `[cli]` — decision 3's whole reason for
        having two roots rather than one.
        """
        if key not in MCP_KEYS:
            raise FuxError(f"`{key}` is not an output key for `mcp` — it has: {sorted(MCP_KEYS)}")
        if tool_value is not None:
            return tool_value
        if self.bypass:
            return BUILT_IN[key]
        if key in self.mcp:
            return self.mcp[key]
        raise FuxError(
            f"{OUTPUT_NAME} does not set `{key}` under [mcp] — add "
            f"`{key} = {BUILT_IN[key]!r}`. Run `fux output` to see every key, "
            "or pass --no-output-config to bypass this file."
        )


#: The bypass sentinel: `--no-output-config`, or no repo root at all.
DEFAULT_OUTPUT = OutputDefaults(bypass=True)


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

    This file is committed, so it can arrive conflicted from a pull.
    """
    for marker in ("<<<<<<<", "=======", ">>>>>>>"):
        if any(line.startswith(marker) for line in text.splitlines()):
            raise FuxError(
                f"{path}: unresolved merge conflict markers — resolve the conflict before fux reads it"
            )


def _checked(c: _Collector, table: str, key: str, value: object) -> object | None:
    """Validate one key/value against `_TYPES`. Returns `None` when rejected."""
    want = _TYPES[key]
    if want is bool:
        if not isinstance(value, bool):
            c.add(f"[{table}] {key} must be true or false (got {value!r})")
            return None
        return value
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


def _verb_owning(key: str) -> str | None:
    """The single verb `key` belongs to, if exactly one does — else `None`."""
    owners = [v for v, keys in CLI_VERBS.items() if key in keys]
    return owners[0] if len(owners) == 1 else None


def _parse_cli_scalars(c: _Collector, table_label: str, scope: dict, out: dict, *, verb: str | None) -> None:
    """Validate the scalar (non-table) entries of one `[cli...]`-family table.

    `verb=None` for a shared table (`[cli]`, `[cli.json]`); `verb=<name>` for
    a per-verb subtable (`[cli.<verb>]`, `[cli.json.<verb>]`) — the closed key
    set differs (a per-verb table may use only that verb's own keys; a shared
    table may use anything reachable from more than one verb).
    """
    in_json = "json" in table_label
    allowed_here = set(CLI_VERBS[verb]) if verb is not None else set(_SHARED_CLI_KEYS)
    if in_json:
        allowed_here = allowed_here | {"enabled"}
    for key, value in scope.items():
        if isinstance(value, dict):
            continue  # a subtable — handled by the caller, not here
        if key in _REFUSED:
            c.add(f"[{table_label}] `{key}` is refused: {_REFUSED[key]}")
            continue
        if key == "enabled" and not in_json:
            # `enabled` only means something inside a `[cli.json...]` table;
            # `table_label` already tells us which family we are in.
            c.add(f"[{table_label}] `enabled` only applies inside `[cli.json]` — it is not a `[cli]` key")
            continue
        if key not in allowed_here:
            owner = _verb_owning(key)
            if owner and verb is not None and verb != owner:
                c.add(f"[{table_label}] `{key}` is a key of {owner}, not of `{verb}`")
            elif owner and verb is None:
                c.add(f"[{table_label}] `{key}` belongs to one verb only ({owner}) — write it under [cli.{owner}] or [cli.json.{owner}]")
            else:
                c.add(f"[{table_label}] unknown key `{key}` — known: {sorted(allowed_here)}")
            continue
        checked = _checked(c, table_label, key, value)
        if checked is not None:
            out[key] = checked


def _parse_cli_root(c: _Collector, root_label: str, table: dict, shared_out: dict, verb_out: dict) -> None:
    """Parse `[cli]` or `[cli.json]`: shared scalars plus per-verb subtables."""
    _parse_cli_scalars(c, root_label, table, shared_out, verb=None)
    for key, value in table.items():
        if key == "json":
            continue  # `[cli.json]` — parsed separately by the caller
        if not isinstance(value, dict):
            continue  # scalar — already handled above
        verb = key
        if verb not in CLI_VERBS:
            c.add(f"[{root_label}] `{verb}` is not a known verb — known: {sorted(CLI_VERBS)}")
            continue
        inner: dict[str, object] = {}
        _parse_cli_scalars(c, f"{root_label}.{verb}", value, inner, verb=verb)
        if inner:
            verb_out[verb] = inner


def _parse(path: Path, data: dict) -> OutputDefaults:
    c = _Collector(path)

    # A file in the OLD flat layout (`[defaults]`, or a bare `[<verb>]` table
    # at the top level) parses cleanly under this grammar and would mean
    # something else — named, not shrugged at (ADR-TUNE's `_LEGACY_FIELD_KEYS`
    # precedent).
    if "defaults" in data and not isinstance(data.get("cli"), dict):
        c.add("[defaults] is the old layout — output keys now live under [cli] (shared) or [cli.<verb>] (per verb). Run `fux output` for the new specimen.")
    for legacy_verb in CLI_VERBS:
        if legacy_verb in data and not isinstance(data.get("cli"), dict):
            c.add(f"[{legacy_verb}] at the top level is the old layout — move it to [cli.{legacy_verb}]. Run `fux output` for the new specimen.")

    for key, value in data.items():
        if key in _ROOTS:
            continue
        if key == "defaults" or key in CLI_VERBS:
            continue  # already reported above, as the legacy-layout message
        if not isinstance(value, dict):
            if key in _SHARED_CLI_KEYS or key == "enabled":
                c.add(f"`{key}` is a key, not a table — did you mean `[cli]\\n{key} = ...`?")
            else:
                c.add(f"`{key}` is not a known key at all — known tables: {sorted(_ROOTS)}")
            continue
        c.add(f"unknown table `[{key}]` — known: {sorted(_ROOTS)}")

    cli_shared: dict[str, object] = {}
    cli_verb: dict[str, dict[str, object]] = {}
    json_shared: dict[str, object] = {}
    json_verb: dict[str, dict[str, object]] = {}
    mcp_out: dict[str, object] = {}

    cli_table = data.get("cli")
    if cli_table is not None:
        if not isinstance(cli_table, dict):
            c.add("`cli` must be a table — write `[cli]`, not `cli = ...`")
        else:
            _parse_cli_root(c, "cli", cli_table, cli_shared, cli_verb)
            json_table = cli_table.get("json")
            if json_table is not None:
                if not isinstance(json_table, dict):
                    c.add(f"[cli] `json` is refused: {_REFUSED['json']}")
                else:
                    _parse_cli_root(c, "cli.json", json_table, json_shared, json_verb)

    mcp_table = data.get("mcp")
    if mcp_table is not None:
        if not isinstance(mcp_table, dict):
            c.add("`mcp` must be a table — write `[mcp]`, not `mcp = ...`")
        else:
            for key, value in mcp_table.items():
                if key in _MCP_REFUSED:
                    c.add(f"[mcp] `{key}` is refused: {_MCP_REFUSED[key]} — UNCONDITIONAL, by name")
                    continue
                if key not in MCP_KEYS:
                    c.add(f"[mcp] unknown key `{key}` — known: {sorted(MCP_KEYS)}")
                    continue
                checked = _checked(c, "mcp", key, value)
                if checked is not None:
                    mcp_out[key] = checked

    c.raise_if_any()
    return OutputDefaults(
        cli_shared=cli_shared,
        cli_verb=cli_verb,
        json_shared=json_shared,
        json_verb=json_verb,
        mcp=mcp_out,
        bypass=False,
    )


def load(root: Path, *, enabled: bool = True) -> OutputDefaults:
    """Read `.fux/output.toml`.

    `enabled=False` is `--no-output-config`: the file is not read at all, and
    every key resolves to `BUILT_IN` — the "is it me or the config?" switch,
    and the one path that still works when the file is what is broken.

    Otherwise the file is now **required to exist and to cover every key a
    caller actually resolves** — see the module docstring. A missing file is
    a `FuxError` here, at load time, with the fix (`fux setup` / `fux output`)
    named in the message; a file that exists but omits one key is a
    `FuxError` later, from `resolve()`/`resolve_json()`/`resolve_mcp()`, once
    it is clear which key and which verb.
    """
    if not enabled:
        return DEFAULT_OUTPUT

    path = root / OUTPUT_NAME
    if not path.is_file():
        raise FuxError(
            f"{path} is missing — run `fux setup` to create it (or, in an "
            f"existing repo, `fux output > {OUTPUT_NAME}`). Pass "
            "--no-output-config to use the engine defaults instead."
        )

    # Windows editors write a BOM; `tomllib.load` reads binary and fails with
    # a decode error that names nothing useful. Stripped rather than diagnosed.
    text = path.read_bytes().decode("utf-8-sig")
    _reject_conflict_markers(path, text)

    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc

    return _parse(path, data)


def specimen() -> str:
    """The file `fux setup` writes (write-if-missing) and `fux output` prints.

    ⚠ **Live lines, not comments** (ADR-OUTPUT decision 14, ruled by Arpit
    2026-08-27, and now load-bearing rather than cosmetic: since 2026-08-28 a
    key this file does not set is a hard error, so a specimen that shipped
    fully commented would break every verb on the very first run after
    `fux setup`). Every value equals its entry in `BUILT_IN` — a fresh repo
    behaves identically to one that never had this file, because both go
    through the same numbers, just by different roots (this file, vs.
    `--no-output-config`'s bypass).
    """
    lines = [
        "# .fux/output.toml — HOW a result is SHOWN. Never which documents come back.",
        "#",
        "# Written once by `fux setup`; fux never rewrites it. Every value below is",
        "# LIVE — it is what the engine already does, restated so you can see it and",
        "# change it. Deleting a line does not restore a hidden default: the file is",
        "# the only source of truth, and a verb that needs a key this file does not",
        "# set will refuse to guess (`fux output` reprints this if you need it back).",
        "#",
        "# Three roots, one per consumer:",
        "#   [cli]       a person reading stdout",
        "#   [cli.json]  a machine reading --json  (inherits [cli]; `enabled` switches it on)",
        "#   [mcp]       an agent over MCP          (inherits NOTHING from [cli])",
        "#",
        "# Precedence, highest first:  a CLI flag  ->  [cli.json.<verb>]  ->  [cli.json]",
        "#   ->  [cli.<verb>]  ->  [cli]              (and, for MCP:  tool arg  ->  [mcp])",
        "#",
        "# Per-verb overrides go under [cli.<verb>] / [cli.json.<verb>] — e.g. an",
        "# uncommented",
        "#   [cli.find]",
        "#   band = false        # find pipes bare paths; a band on stdout would break that",
        "#",
        "# `fux ask --no-output-config` ignores this whole file — the",
        '# "is it me or the config?" switch.',
        "",
        "# `band` and `top` are shared by more than one verb, so they live here.",
        "# A key only one verb has (`explain`, `hops`, `no_refer`, `journal`) is",
        "# refused at this level BY NAME — it lives under that verb's own table,",
        "# below — setting it here would read as global, and it is not.",
        "[cli]",
        f"band = {str(bool(BUILT_IN['band'])).lower()}       # the confidence block — ADR-CONFIDENCE decision 11",
        f"top = {int(BUILT_IN['top'])}            # ask/find. ⚠ also bounds `confidence.support`,",
        "               #   which is a REPORTED signal — the one key here that",
        "               #   changes a number an agent reads, admitted rather than hidden.",
        "",
        "[cli.ask]",
        f"explain = {str(bool(BUILT_IN['explain'])).lower()}    # report which path answered",
        "",
        "[cli.path]",
        f"hops = {int(BUILT_IN['hops'])}          # max edges in a route",
        "",
        "[cli.answer]",
        f"no_refer = {str(bool(BUILT_IN['no_refer'])).lower()}",
        f"journal = {str(bool(BUILT_IN['journal'])).lower()}    # record each answer's receipt locally",
        "",
        "[cli.json]",
        f"enabled = {str(bool(BUILT_IN['json'])).lower()}   # emit --json by default; per-verb: [cli.json.<verb>] enabled = true",
        "",
        "[mcp]                # the one surface with NO command-line flags at all —",
        "                     # this table is the only way to configure it.",
        f"top = {int(BUILT_IN['top'])}            # ⚠ no `band` here: the MCP confidence block is",
        "               #   UNCONDITIONAL (ADR-CONFIDENCE decision 11), refused by name.",
        "",
    ]
    return "\n".join(lines) + ("\n" if not lines[-1] else "")
