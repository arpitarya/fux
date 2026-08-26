---
type: OpenItem
id: W-85
title: "W-85 — max_parallel is a required key: never commented, and a missing one is an error"
description: "Arpit, 2026-08-26, ruling directly on W-83's output: 'never commented. If it is commented, throw an error that the value has to be present.' W-83 put the concurrency bound into the fux.toml template as a COMMENTED line inside a commented [sources.url] table, so the property a consumer was meant to see was still invisible. This makes it live in what setup writes, required by the loader, and self-migrating for existing files — a live [sources.url] without it refuses to load and says what to add."
status: closed
lane: agent
timestamp: 2026-08-26T00:00:00Z
---

# W-85 — `max_parallel` is a required key

> ## ✅ CLOSED 2026-08-26, filed and built in one session.
>
> All eight boxes in §3 met. **The property is live in what `fux setup` writes,
> live in this repo's own `fux.toml`, and required by the loader** — so an
> existing file that lacks it refuses on the next command and says what to add.
>
> **Outcome:** [`IMPLEMENTATION.md`](../IMPLEMENTATION.md). **Records:**
> ADR-CONFIG and ADR-DOTFUX, amended in the same change.
>
> ⚠ **The one thing worth carrying past this item**, recorded in ADR-DOTFUX:
> **a change to a write-if-missing template is a change for new repos only.**
> W-83 believed it had shipped a config property and had shipped it to nobody
> who already had a `fux.toml`. If a template change must reach existing
> repos, the mechanism is a **loader refusal or a `doctor` check** — never a
> rewrite, which would eat a consumer's annotations.

**Model: Sonnet.** The ruling is Arpit's and is quoted below; what remains is a
loader change, a template change, and the fixtures and records that follow.

**Records:** [ADR-CONFIG](../../docs/adr/0014_config.md) (the key and its
requiredness) · [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) (what
`fux setup` writes).

---

## 1 · What W-83 got wrong

W-83 closed having *"exposed the property in `fux.toml`"*. It did not.

The line it added was `#max_parallel = 4` — **commented, inside an already
commented `[sources.url]` table**. A consumer opening `fux.toml` saw a comment
about a number, not a number. Arpit's response on reading it:

> **"I wanted a property exposed. Where is that property? It should be present
> by default."**
>
> **"never commented. If it is commented, throw an error that the value has to
> be present."**

**A second, separate failure surfaced at the same time.** `fux setup` is
write-if-missing (ADR-DOTFUX), so it never rewrote an existing `fux.toml` —
meaning **this repo's own config, and every existing user's, gained nothing at
all** from W-83. A template-only fix reaches new repos and no one else.

## 2 · The decision

**`[sources.url] max_parallel` is REQUIRED whenever `[sources.url]` exists.**

| case | behaviour |
|---|---|
| `[sources.url]` live, `max_parallel` live | its value, validated as before |
| `[sources.url]` live, `max_parallel` absent or commented | **`FuxError`**, naming the key and the value to add |
| `[sources.url]` absent entirely | **no error** — no URL source exists, so there is no fetching to bound |

**The third row is the line this draws, and it is deliberate.** A docs-only
repo that never fetches anything must not be forced to declare a fetch bound;
requiring one there would make the key noise, and noise is how a safety value
stops being read. What is forbidden is a repo that *can* fetch and does not say
how hard.

**Requiredness is what reaches existing files.** A template cannot migrate a
file `setup` will never touch again — but a **loader error can**, because it
puts the key in front of the person on their next command, with the value to
type. That is the only mechanism available that does not rewrite a file a
consumer may have annotated.

⚠ **`fux setup` now writes `[sources.url]` LIVE**, which is the other half of
"present by default" and **changes one behaviour**: `fux add <URL>` previously
recorded the line and printed *"no `[sources.url]` in fux.toml, so nothing can
fetch this line yet"*; in a repo scaffolded after this change it fetches. **The
gate does not disappear — it moves to where it always really was**,
`.fux/sources/urls` being empty. Nothing is fetched until a URL is listed, and
a URL is listed only by an explicit `fux add`. L4's *explicit, fenced, opt-in*
is satisfied by the verb rather than by a commented table.

## 3 · Definition of done

1. `UrlSource.max_parallel` is `int`, not `int | None`. The loader raises when
   `[sources.url]` is present without it.
2. The error names the key, says it must be present, and gives a value to
   paste — an error that does not say what to type is half a migration.
3. `fux setup` writes `[sources.url]` and `max_parallel` **live**, the number
   still interpolated from `DEFAULT_MAX_PARALLEL`.
4. **This repo's own `fux.toml` is updated by hand**, because nothing else will.
5. Every fixture writing a bare `[sources.url]` gains the key.
6. `fux doctor`'s "max_parallel unset" branch is unreachable from config and is
   removed rather than left as dead reassurance.
7. ADR-CONFIG and ADR-DOTFUX amended in the same change.
8. `uv run pytest -q tests` green but for the known 3.10-shim failures.

## 4 · Hazards

- **`DEFAULT_MAX_PARALLEL` stays**, and `resolve_parallel(module, None)` keeps
  working: config no longer passes `None`, but the function is called directly
  by tests and by any programmatic caller, and deleting the safe path to
  celebrate a required key would trade one silent default for one crash.
- **Do not require the key when `[sources.url]` is absent.** See §2 row three.
- **Do not make `fux setup` rewrite an existing `fux.toml`.** Write-if-missing
  is ADR-DOTFUX's promise and the reason `fux tune` prints rather than edits;
  the loader error is the migration path, not a rewrite.
