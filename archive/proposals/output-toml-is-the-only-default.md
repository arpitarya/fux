# `.fux/output.toml` is the only place a default exists

**Status:** ruled by Arpit, 2026-08-27. Not yet built.
**Amends:** ADR-OUTPUT (`docs/adr/0047_output-defaults.md`) decisions 1, 2, 6, 10, 14, 15, 16, 18.
**Written by:** Cowork, from a session with **no shell** (`device_bash` failed 5/5) and with a
**concurrent live session editing `src/fux/`** — `mcp.py` changed twice while this was being
written. Nothing in `src/` was touched. This document is the handoff.

---

## 1. The complaint that started it

`fux setup` writes a `.fux/output.toml` in which **every key is commented out**. Arpit has now
said this twice. The file is meant to be *the* declaration of what fux does; it currently reads
as a menu of things it might do.

**The ADR already agrees.** Decision 14 says, in the record, dated 2026-08-27:

> ⚠ **The specimen carries LIVE lines, not comments. Ruled by Arpit, 2026-08-27** — the same
> ruling `.fux/sources/types` got the same day … *a file of nothing but comments is a menu, and
> a consumer should be able to read what fux will do without reading fux's source.*

`tune.py`'s `specimen()` implemented that ruling. `output_config.py`'s did not. This is the
**W-83 defect class exactly** — an accepted decision that the code never followed, and that no
test can see, because every test was written against the code.

---

## 2. What Arpit ruled, in his words

> There shouldn't be anything built in. Everything should be coming from output.toml. All the
> defaults at least. If explicit flags are passed in CLI, it will override the TOML file.
> Defaults has the lowest priority. Specific ones like specific verbs — ask, find, MCP — have
> higher priority. CLI flags have the highest priority.
>
> MCP defaults don't apply to it. MCP only depends on the MCP table. Nothing else. And it
> shouldn't have anything by default. Everything that an agent needs, MCP should serve it.
> Explicitly defining one means we are trying to block it. That will be the only purpose to
> define it in the table.

Plus, answering the two forks put to him:

- **The file is REQUIRED.** Absent → fux refuses loudly. No packaged fallback.
- **`[mcp] top` is spelled out, not left empty**, and its shipped value is `"all"` — a named
  sentinel meaning *serve the whole ranked set*.

---

## 3. The design

### 3.1 There are TWO precedence chains, not one

```
CLI verbs   CLI flag  →  [<verb>]  →  [defaults]
MCP         tool-call `k`  →  [mcp]
```

`[defaults]` **never reaches `[mcp]`.** That is the whole point of the split: a line someone
wrote for their terminal must not silently retune a server an agent is talking to.

There is **no fourth step**. `output_config.BUILT_IN` is deleted. No number typed into a Python
file is a default any more.

### 3.2 The file is required

- `.fux/output.toml` absent → `FuxError`, naming the fix: `fux output > .fux/output.toml`
  (byte-identical to what `fux setup` writes).
- No fallback, no silent defaults, no warning-and-continue.
- **Cost, stated not hidden:** every repo that ran `fux setup` before this change refuses on the
  next `fux ask` until the file is written. That is the same trade `fux.toml`'s `max_parallel`
  already makes — *a repo that does a thing has to say how, in a number a person can read.*

### 3.3 Completeness is validated at LOAD, not discovered at resolve

For every `(verb, key)` in `SCHEMA`, the value must be resolvable:

| verb | resolvable from |
|---|---|
| `mcp` | `[mcp]` **only** |
| every other verb | `[<verb>]`, else `[defaults]` |

A key that resolves from neither is a **loud load-time error listing every missing pair at once**
(the existing `_Collector` already batches to 10). Not a lazy failure at the moment someone runs
the one verb that needed it.

This is what makes `[defaults]` real rather than decoration: verb tables are allowed to omit a
key precisely *because* `[defaults]` will answer for it.

### 3.4 The shipped file

Live lines everywhere. Shared keys stated once, in `[defaults]`. A verb table carries only what
is its own — plus a comment naming what it inherits and may override.

```toml
# .fux/output.toml — HOW a result is SHOWN. Never which documents come back.
#
# ⚠ THIS FILE IS REQUIRED. There are no built-in defaults; every value fux uses
# is a line in this file. Delete it and fux refuses and tells you so. Restore it
# with `fux output > .fux/output.toml`.
#
# Written once by `fux setup`; fux never rewrites it.
#
# TWO precedence chains, and the second one is why this file is not one table:
#
#   CLI verbs   a CLI flag  →  [<verb>]  →  [defaults]
#   MCP         the tool call's `k`  →  [mcp]
#
# ⚠ [defaults] NEVER REACHES [mcp]. A line you wrote for your terminal may not
# retune a server an agent is talking to.
#
# The rule for what may live here is mechanical: changing any value below leaves
# the ranked result set AND ITS ORDER identical. It changes what is emitted,
# never what is computed. (.fux/tune.toml changes ordering; fux.toml changes
# what is indexed.)

[defaults]                # the LOWEST priority, and only keys more than one verb has
json = false
band = false              # the confidence block — ADR-CONFIDENCE decision 11
top  = 5                  # ⚠ also bounds `confidence.support`, a REPORTED signal.
                          #   The one key here that changes a number an agent reads,
                          #   admitted rather than hidden.

[ask]                     # also takes json, band, top from [defaults] — state one
                          # here to override it for `ask` alone
explain = false

[find]                    # takes json, band, top from [defaults]
                          # ⚠ `find` pipes bare paths; `band = true` here would
                          #   break that

[answer]                  # takes json, band from [defaults]
no_refer = false
journal  = false          # record each answer's receipt to the local, gitignored
                          # journal. ⚠ OFF, deliberately: a $0 offline tool may not
                          # quietly begin recording questions because a config line
                          # exists. `--journal` is still the per-run switch.

[explain]                 # takes json from [defaults]

[graph]                   # takes json from [defaults]
                          # ⚠ no `top` — ADR-OUTPUT decision 18: truncating a walk
                          #   changes WHICH nodes come back, which this file may not do

[path]                    # takes json from [defaults]
hops = 2

[doctor]                  # takes json from [defaults]

[hooks]                   # takes json from [defaults]

[daemon]                  # takes json from [defaults]

[mcp]                     # ⚠ READS NOTHING FROM [defaults]. This table is all of it.
                          # An agent gets everything unless a line here BLOCKS it —
                          # that is the only reason to write one.
top = "all"               # the whole ranked set. A number caps what an agent may
                          # receive; `k` in the tool call still narrows one call.
                          # ⚠ Cost: a broad query on a large corpus hands the agent
                          #   the whole ranked set and burns its context. The
                          #   throttle exists — it is off until someone asks.
```

### 3.5 `top = "all"`

- Legal **only in `[mcp]`**. In `[defaults]`, `[ask]`, `[find]` it is refused **by name with the
  reason**: a terminal has a human and a pager; an agent has neither, and `"all"` there is a
  paging problem wearing a config line. *(Open to reversal — see §6.)*
- Validator: `[mcp] top` is `int ≥ 1` **or** the literal string `"all"`. The `bool`-before-`int`
  guard stays exactly as it is.
- `_search`: no cap when `"all"`; an explicit `k` in the tool call still wins.
- **`tools/list` must stay honest (decision 16).** With `"all"`, the `k` schema carries **no**
  `default` and its description says the full ranked set is returned when `k` is omitted. With
  `[mcp] top = 50` it advertises `50`. An advertised number that the server does not use is the
  W-83 defect again.

### 3.6 `fux doctor` must not be the verb that can't run

`doctor` declares `json`, so under §3.2 a missing `output.toml` would make **the one verb you'd
run to diagnose a missing `output.toml`** refuse. That is ADR-OUTPUT decision 15's *"a surface
you cannot bisect is a surface you cannot debug"*, in reverse.

`doctor` therefore **reports a missing or invalid `output.toml` as a finding and keeps going**,
in human mode, naming `fux output > .fux/output.toml`. It is the one exemption, and it is
exempted because it is the diagnostic.

---

## 4. Everything that has to change

### `src/fux/output_config.py`
1. Delete `BUILT_IN`. Every default is a line in the shipped TOML.
2. `SCHEMA["graph"]` → `("json",)`. The `top` there is dead: `graph` has no `--top` flag, and
   `_apply_output_defaults` skips keys with no matching attr — so `[graph] top = 10` validates
   today and does nothing. **ADR decision 18 already says it was removed. It wasn't.**
3. `load(root)`: missing file → `FuxError` naming `fux output > .fux/output.toml`.
4. Add the completeness pass of §3.3.
5. `resolve(verb, key, cli_value)`: chain stops at `[defaults]`. No built-in tail.
6. Add `resolve_mcp(key)`: `[mcp]` only. **`mcp.py` already calls this method and it does not
   exist** — see §5.
7. `specimen()` → the live file of §3.4. Docstring rewritten: it is now *the* defaults, not a
   menu, and the freeze cost is stated (setup is write-if-missing, so the values freeze at setup;
   remedy is a loader refusal or a `fux doctor` check, **never a rewrite** — ADR-DOTFUX d6).

### `src/fux/cli.py`
8. `_top_help()` / `_hops_help()` no longer cite a number — there is none to cite. e.g.
   `"max results (default: [defaults] top in .fux/output.toml)"`.
9. `_apply_output_defaults`: the no-repo branch currently resolves against `DEFAULT_OUTPUT`.
   With no built-ins that branch has no answer — decide it with §6.

### `src/fux/mcp.py`
10. `_resolve` → `defaults.resolve_mcp(key)` against the new method (it is already written this
    way; the method is what's missing).
11. `_tools(top)` handles `"all"` per §3.5.
12. `_search` treats `"all"` as no cap.

### `src/fux/setup.py`
13. No change beyond the new `specimen()` — it already writes it, write-if-missing.

### `docs/adr/0047_output-defaults.md`
14. Amend decisions 1, 2, 6, 10, 14, 15, 16, 18; add the required-file rule, the two chains, the
    `"all"` sentinel and the `doctor` exemption. **ADR currency law: same commit, not a
    follow-up.**

### Tests
15. `tests/test_output_config.py` — `test_the_specimen_parses_and_is_entirely_commented_out`
    **inverts**: the specimen must be live and must resolve to the documented values. Add:
    absent file refuses; an incomplete file names every missing pair; `[defaults]` does **not**
    reach `[mcp]`; `[mcp] top = "all"`; `"all"` refused outside `[mcp]`; `[graph] top` is now an
    unknown key.
16. `tests/test_setup.py` — what setup writes must `load()` clean and be complete.
17. `tests/test_cli.py` — help text no longer carries a literal.
18. `tests/test_mcp.py` — `tools/list` under `"all"` and under a number.
19. Delete `test_every_built_in_is_reachable_from_some_verb` and
    `test_every_schema_key_has_a_built_in`; replace with *every schema key is stated in the
    shipped file*.

---

## 5. Three things found while reading, unrelated to the ruling

- **`fux mcp` is broken right now.** `mcp._resolve` calls `defaults.resolve_mcp(key)`.
  `OutputDefaults` has no such method — it has `resolve`. `AttributeError` on the first
  `tools/list`. `mcp.py` also documents a `[cli]` table that `SCHEMA` does not have. The two
  files are mid-flight against each other. *(A live session was editing `mcp.py` while this was
  written — it may already be fixed.)*
- **`[graph] top` is a dead key** the ADR already declared removed. §4.2.
- **`docs/adr/0047_fuxignore.md` is a stray** — two records claim 0047, and it is keeping two ADR
  tests red. Already named in `work/BLOCKED.json`: `git rm docs/adr/0047_fuxignore.md`.

---

## 6. The one open question

**What does `--no-output-config` mean once there are no built-ins?**

The flag exists to answer *"is it me or the config?"* — it needs something to fall back to, and
under this ruling there is nothing.

| option | consequence |
|---|---|
| **A (recommended)** — it resolves against the **shipped reference TOML** (what `fux output` prints) | the bisect switch keeps working; still no hand-typed number anywhere — the reference is itself a TOML string in the package. But it is a fallback, which is what the ruling refused. |
| **B** — **remove the flag.** Bisecting becomes `fux output > /tmp/ref.toml` and a diff | truest to *the file is the only source*; costs the one-flag bisect that ADR-OUTPUT decision 15 was written to protect. |

Same question decides `cli._apply_output_defaults`'s no-repo branch (§4.9).

---

## 7. Paste-ready prompt for Claude Code

> **Model: Opus.** The loader redesign and the ADR amendment are judgement calls with a live
> record to keep consistent; decisions 14 and 18 were already lost once by an agent that treated
> the ADR as prose. Do not run this on Sonnet. The mechanical test edits in step 5 can be
> delegated to Sonnet *after* steps 1–4 are reviewed.

```
Read work/proposals/output-toml-is-the-only-default.md end to end, then
docs/adr/0047_output-defaults.md and src/fux/output_config.py.

Arpit has ruled that .fux/output.toml is the ONLY place a default value exists.
Implement §3 and §4 of the proposal. Before you write anything:

1. ANSWER §6 by asking Arpit — do not pick for him. It changes two call sites.
2. `git status` first. A concurrent session was editing src/fux/mcp.py and
   src/fux/output_config.py on 2026-08-27; re-read both from disk before every
   write and do not commit anything you did not just read.

Then, in this order, and stop after each for review:

1. output_config.py — delete BUILT_IN, drop SCHEMA["graph"]["top"], make the
   file required, add the load-time completeness pass, add resolve_mcp(),
   rewrite specimen() to the live file in §3.4.
2. mcp.py — resolve_mcp wiring, `top = "all"` in _search and in _tools()'s
   advertised `k` schema (decision 16: never advertise a number you do not use).
3. cli.py — help text with no literal; the no-repo branch per §6.
4. docs/adr/0047_output-defaults.md — amend decisions 1, 2, 6, 10, 14, 15, 16,
   18 and add the new ones. SAME COMMIT as the code. ADR currency law.
5. tests — §4.15 through §4.19.

Then run the full suite and report pass/fail counts. Also `git rm
docs/adr/0047_fuxignore.md` (a stray duplicate number keeping two ADR tests red)
and confirm the ADR register is unchanged.

Do not add a built-in default anywhere, in any file, for any reason. If a code
path needs a number and the file has not supplied one, that is a refusal, not a
fallback.
```
