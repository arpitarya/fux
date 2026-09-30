"""`.fux/output.toml` — output defaults, in three roots, one per consumer.

**The boundary, unchanged from the first build of this record.** A key
belongs here iff changing it leaves the ranked result set *and its order*
identical — it may change what is printed, never what is computed. `fux.toml`
asks *what is indexed*; `.fux/tune.toml` asks *which documents come back, or
their order*; this file asks *how are they shown*. `top` is the one admitted
boundary case: it truncates a ranking (allowed) and it bounds
`confidence.support`, a REPORTED signal (stated, not hidden).

## Three roots, because there are three consumers (SR-OUTPUT decision 3)

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
      FuxError -- the key is missing; `fux doctor --fix` writes it

  The FILE read is the repo's `.fux/output.toml`; under --no-output-config, or
  with no repo root at all, it is the packaged template `fux setup` writes.
```

## The file is the sole source of truth, and it must exist (L12)

**Every key a verb resolves comes from a file, never from code.** In a repo it
is `.fux/output.toml`; a missing file, table or key is a `FuxError` naming it
and the remedy, `fux doctor --fix`, which writes exactly the missing keys from
the template ([L12](../../records/0014_LAW-12-values-live-in-config.md)
decision 3). `--no-output-config` — the "is it me or the config?" switch — and
a run outside any repo read the packaged template, `templates/output.toml.txt`,
which is the one home of every shipped rendering value. There is no built-in
dict behind any of them.

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
from .constants import fixed

__all__ = [
    "OUTPUT_NAME",
    "OutputDefaults",
    "CLI_VERBS",
    "MCP_KEYS",
    "API_KEYS",
    "load",
    "specimen",
    "template",
    "template_text",
]

#: Committed, and written once by `fux setup`, exactly as `tune.toml` is.
OUTPUT_NAME = fixed("files", "output")

#: At most this many semantic errors are reported together.
_MAX_REPORTED = 10

#: The two top-level roots. Anything else at the top of the file is unknown.
_ROOTS = ("cli", "mcp", "api")

#: The closed key set for the `[cli]` / `[cli.json]` roots, per verb. A key
#: here reaches a verb through `[cli.<verb>]` / `[cli.json.<verb>]`, or
#: through the shared `[cli]` / `[cli.json]` table if the verb declares it.
#:
#: ⚠ **`graph` has no `top` key.** It had a dead one on the first build:
#: `graph` has no `--top` flag and reads `seed_depth`/`expand_limit` from
#: `.fux/tune.toml` instead — truncating a graph walk is a ranking change,
#: which this file may not make (SR-OUTPUT decision 18).
#:
#: `json` is deliberately absent from every tuple below: it is not a `[cli]`
#: key at all, it is the question of WHICH chain the other keys walk
#: (`resolve_json`), answered once per call before any of these are touched.
CLI_VERBS: dict[str, tuple[str, ...]] = {
    "ask": ("band", "top", "explain", "sections", "max_headings"),
    # 🔴 **`lexical` carries `ask`'s keys EXACTLY, and omitting it was a live
    # bug for the length of one smoke test** (W-160). `fux lexical` is frozen
    # byte-identical to `ask`; a verb absent from this table has no key
    # resolved at all, so `args.sections` stayed `None`, `getattr(args,
    # "sections", True)` read it as falsy, and `lexical` printed no `§`
    # heading lines while `ask` printed them. **Two verbs, same ranking,
    # different output — the exact divergence the freeze exists to forbid**,
    # and nothing failed: the file loaded, the query ran, the answer was right.
    # This is W-140 row 14's trap (an absent entry never resolves `--json`)
    # arriving through a different door.
    "lexical": ("band", "top", "explain", "sections", "max_headings"),
    "find": ("band", "top", "max_headings"),
    # `journal_max` since L12 (W-225): how many receipts the journal keeps.
    "answer": ("band", "no_refer", "journal", "journal_max"),
    "explain": (),
    "graph": (),
    "path": ("hops",),
    "doctor": ("progress_threshold",),
    "hooks": (),
    "daemon": (),
    # `ingest` has no `[cli.ingest]` key of its own — only `--json` to resolve,
    # like `doctor` and `hooks`. An EMPTY tuple is the declaration that this
    # verb is shaped by this file; an absent entry means it is not, and
    # `--json` would then never be resolved from `[cli.json]` (W-140 row 14).
    # ⚠ **It arrived with `--check --json` on `fux update` and moved here whole
    # when W-177 deleted that verb.**
    "ingest": ("progress_threshold",),
    # ⚠ **`update` had this row until W-177 deleted the verb** (2026-09-15).
    # It is not missing — `ingest` absorbed `--check --json`, so `ingest`
    # carries the row now, above.
    # `inspect` carries no `[cli.inspect]` key of its own — only `--json` to
    # resolve, like `doctor` and `ingest`. The EMPTY tuple is the declaration
    # that this verb IS shaped by this file; an absent entry would leave
    # `--json` unreachable from `[cli.json]` (W-140 row 14, the same trap).
    # `--top` and `--retrieval-sample` stay flags: both are how much WORK to
    # do, not how a result is shown, and SR-OUTPUT's subject is the latter.
    "inspect": ("progress_threshold",),
    # `correct` carries no `[cli.correct]` key of its own — only `--json` to
    # resolve, like `doctor`, `ingest` and `inspect`. An EMPTY tuple is the
    # declaration that this verb IS shaped by this file (W-140 row 14).
    "correct": (),
    # The other three verbs that paint progress (`cli._PROGRESS_COMMANDS`). A
    # verb listed here is shaped by this file; that is what lets the one
    # `Progress` a command builds read its threshold from the file (L12).
    "build": ("progress_threshold",),
    "add": ("progress_threshold",),
    "remove": ("progress_threshold",),
    # W-238: three more verbs that paint progress, each measured slow first.
    "identifiers": ("progress_threshold",),
    "enrich": ("progress_threshold",),
    # `fux serve`'s port. The host is fixed (`constants.toml [serve] host`).
    "serve": ("port",),
}

#: 🔴 **The one verb that reads ANOTHER verb's subtable, and it is a fact about
#: the freeze rather than a convenience** (W-160). `fux lexical` is frozen
#: byte-identical to `fux ask` ([SR-CLI](../../records/0101_cli-surface.md)
#: decision 12), so a consumer's committed `output.toml` must not be able to
#: make the two differ — and `[cli.lexical] sections = false` beside
#: `[cli.ask] sections = true` would do exactly that, silently, with both files
#: valid.
#:
#: ⚠ **The alternative was a breaking change to every existing file.** This
#: file is a **complete declaration** (decision 20's companion rule): a verb
#: with keys that nothing declares raises. `explain` is unique to `ask`, so it
#: is refused at the shared `[cli]` level by name — which means a `lexical`
#: with its own subtable would have made every repo that already has an
#: `output.toml` exit 1 on a verb they had never run. Measured, not predicted:
#: it happened on this repository the first time `lexical` ran.
#:
#: **It is a map with one entry and no mechanism.** A second entry needs a
#: reason of its own, in this comment, beside the first.
VERB_READS: dict[str, str] = {"lexical": "ask"}


def subtable_for(verb: str) -> str:
    """Whose `[cli.<verb>]` subtable this verb resolves through.

    Identity for every verb but `lexical` — see `VERB_READS`. Kept a function
    so both `resolve` and `resolve_json` walk the same answer; two lookups is
    how one of them would forget.
    """
    return VERB_READS.get(verb, verb)


#: `[mcp]`'s closed key set. `top` only — decision 11. No `json` (an MCP
#: result is always JSON) and, corrected during the first build, no `band`
#: (SR-CONFIDENCE decision 11 makes the confidence block unconditional over
#: MCP precisely because a tool call cannot pass a flag).
MCP_KEYS: tuple[str, ...] = ("top", "max_headings")

#: `[api]`'s closed key set -- the Python `fux.open()` and Node `Index` library
#: defaults a caller did not pass (W-225 stage 6, SR-LAW-12 decision 6a R8:
#: where the CLI reads a flag's default from this file, the API reads it here
#: too). Its own root, like `[mcp]`: the library ships `band` and `sections`
#: ON where the CLI ships them off, deliberately -- a caller in code has already
#: decided to read the object, and the block says whether to trust it.
API_KEYS: tuple[str, ...] = ("band", "sections", "no_refer")


#: Every key `[cli]` / `[cli.json]` may carry at the shared (non-per-verb)
#: level: keys that more than one verb declares. A key unique to one verb
#: (`explain`, `no_refer`, `journal`, `hops`) is refused at the shared level
#: **by name** — setting it there reads as global and is not — and belongs
#: under that verb's own subtable instead (`[cli.ask]`, `[cli.path]`, ...).
def _keys_shared_by_more_than_one_verb() -> tuple[str, ...]:
    """Keys more than one SUBTABLE declares — not more than one verb.

    ⚠ **Counting verbs would have loosened a validation as a side effect of
    `VERB_READS`.** `explain` and `sections` are `ask`'s alone, and this file
    refuses a single-verb key at the shared `[cli]` level by name, because
    *"setting it there reads as global and is not"*. `lexical` declares the
    same keys and resolves through `ask`'s own subtable, so the two are **one
    declaration in two rows** — and counting rows would have made
    `[cli] explain = true` legal where it had always been refused. Counting
    subtables keeps the refusal exactly where decision 3 put it.
    """
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for verb, keys in CLI_VERBS.items():
        table = subtable_for(verb)
        if table in seen:
            continue  # `lexical` reads `ask`'s row; it is not a second declarer
        seen.add(table)
        for k in keys:
            counts[k] = counts.get(k, 0) + 1
    return tuple(sorted(k for k, n in counts.items() if n > 1))


_SHARED_CLI_KEYS: tuple[str, ...] = _keys_shared_by_more_than_one_verb()

#: Type per key, as spelled IN THE FILE (`enabled`, not `json`). `bool` is
#: checked before `int` everywhere: `isinstance(True, int)` is `True` in
#: Python, so an unguarded check accepts `top = true` and silently means
#: `top = 1`.
_TYPES: dict[str, type] = {
    "band": bool,
    "explain": bool,
    "sections": bool,
    "no_refer": bool,
    "journal": bool,
    "enabled": bool,
    "top": int,
    "hops": int,
    "max_headings": int,
    "progress_threshold": int,
    "journal_max": int,
    "port": int,
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
        "the confidence block is UNCONDITIONAL over MCP (SR-CONFIDENCE "
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
    #: `[api]`'s scalars.
    api: dict[str, object] = field(default_factory=dict)
    #: Where these values were read from — the repo's file, or the packaged
    #: template (`--no-output-config`, or no repo root). Named in every error.
    source: str = ""

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
        per_verb = self.json_verb.get(subtable_for(verb), {})
        if "enabled" in per_verb:
            return bool(per_verb["enabled"])
        if "enabled" in self.json_shared:
            return bool(self.json_shared["enabled"])
        raise FuxError(
            f"{self.source}:\n  [cli.json] enabled is missing\n  {_FIX_HINT}"
        )

    def resolve(self, verb: str, key: str, cli_value: object = None, *, as_json: bool) -> object:
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
        table = subtable_for(verb)
        if as_json:
            per_verb = self.json_verb.get(table, {})
            if key in per_verb:
                return per_verb[key]
            if key in self.json_shared:
                return self.json_shared[key]
        per_verb = self.cli_verb.get(table, {})
        if key in per_verb:
            return per_verb[key]
        if key in self.cli_shared:
            return self.cli_shared[key]
        where = f"[cli.{table}]" if _verb_owning(key) == table else "[cli]"
        raise FuxError(f"{self.source}:\n  {where} {key} is missing\n  {_FIX_HINT}")

    def resolve_mcp(self, key: str, tool_value: object = None) -> object:
        """`[mcp]`'s own chain: **tool arg → `[mcp]` → bypass → error.**

        `[mcp]` inherits nothing from `[cli]` — decision 3's whole reason for
        having two roots rather than one.
        """
        if key not in MCP_KEYS:
            raise FuxError(f"`{key}` is not an output key for `mcp` — it has: {sorted(MCP_KEYS)}")
        if tool_value is not None:
            return tool_value
        if key in self.mcp:
            return self.mcp[key]
        raise FuxError(f"{self.source}:\n  [mcp] {key} is missing\n  {_FIX_HINT}")

    def resolve_api(self, key: str, arg_value: object) -> object:
        """`[api]`'s own chain: **argument -> `[api]` -> error.** It inherits
        nothing from `[cli]`, for `[mcp]`'s reason."""
        if key not in API_KEYS:
            raise FuxError(f"`{key}` is not an output key for `api` — it has: {sorted(API_KEYS)}")
        if arg_value is not None:
            return arg_value
        if key in self.api:
            return self.api[key]
        raise FuxError(f"{self.source}:\n  [api] {key} is missing\n  {_FIX_HINT}")


#: What a missing key's error tells the reader to do — `tune.py`'s sentence.
_FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses"


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
    """The single SUBTABLE `key` belongs to, if exactly one does — else `None`.

    By subtable, for `_keys_shared_by_more_than_one_verb`'s reason: `lexical`
    declares `ask`'s keys and reads `ask`'s row, so the two are one declaration.
    Counting verbs would have made this return `None` for `explain` and
    `sections` — and the error message for `[cli.find] explain = true` would
    have degraded from *"`explain` is a key of ask, not of `find`"* to
    *"unknown key `explain`"*, which sends the reader looking for a typo.
    """
    owners = {subtable_for(v) for v, keys in CLI_VERBS.items() if key in keys}
    return next(iter(owners)) if len(owners) == 1 else None


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
    # something else — named, not shrugged at (SR-TUNE's `_LEGACY_FIELD_KEYS`
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

    api_out: dict[str, object] = {}
    api_table = data.get("api")
    if api_table is not None:
        if not isinstance(api_table, dict):
            c.add("`api` must be a table — write `[api]`, not `api = ...`")
        else:
            for key, value in api_table.items():
                if key not in API_KEYS:
                    c.add(f"[api] unknown key `{key}` — known: {sorted(API_KEYS)}")
                    continue
                checked = _checked(c, "api", key, value)
                if checked is not None:
                    api_out[key] = checked

    c.raise_if_any()
    return OutputDefaults(
        cli_shared=cli_shared,
        cli_verb=cli_verb,
        json_shared=json_shared,
        json_verb=json_verb,
        mcp=mcp_out,
        api=api_out,
        source=str(path),
    )


def load(root: Path | None, *, enabled: bool) -> OutputDefaults:
    """Read `.fux/output.toml` — every key a verb resolves must be in it.

    `enabled=False` is `--no-output-config`, and `root=None` is a run outside
    any repo: both read the packaged template instead — the file `fux setup`
    would write today — never a value in code (L12 decision 7). A missing file
    is an error naming it (L12 decision 3); a missing KEY is reported by
    `resolve()`/`resolve_json()`/`resolve_mcp()`, once it is clear which key a
    verb needs.
    """
    if not enabled or root is None:
        return template()

    path = root / OUTPUT_NAME
    if not path.is_file():
        raise FuxError(
            f"{path} is missing - `fux setup` writes it, and `fux doctor --fix` "
            "restores a deleted one. fux holds no copy of its values in code"
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


def template_text() -> str:
    """`templates/output.toml.txt` — what `fux setup` writes and `fux output` prints."""
    return (Path(__file__).parent / "templates" / fixed("templates", "output")).read_text(
        encoding="utf-8"
    )


#: How the template is named in an error — it is not the consumer's file.
_TEMPLATE_LABEL = "the packaged output.toml template (--no-output-config)"


def template() -> OutputDefaults:
    """The template, parsed — `--no-output-config` and a run outside any repo."""
    return _parse(_TEMPLATE_LABEL, tomllib.loads(template_text()))


def specimen() -> str:
    """The file `fux setup` writes (write-if-missing) and `fux output` prints.

    ⚠ **Live lines, not comments** (SR-OUTPUT decision 14, ruled by Arpit
    2026-08-27): every key a verb resolves must be in the file, so a specimen
    that shipped commented would break every verb on the first run after
    `fux setup`. It is the template, verbatim — the one home of every shipped
    rendering value (L12).
    """
    return template_text()
