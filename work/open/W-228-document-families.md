---
type: Handoff
name: W-228
description: "A `families` lens in `fux inspect` — deterministic grouping of documents by shape (heading skeleton + frontmatter field set + length profile), the misfits that break their family's shape, `--json` for agents, and a panel on the explorer's Index tab. Ratified 2026-09-27, NOT built."
item: W-228
filed: 2026-09-27
ball: agent
---

# W-228 — document families: pattern recognition over the corpus, inside `inspect`

**Status: DoD 1–10 BUILT 2026-09-28 (Claude Code, Opus); DoD 11 open.** The lens, the report section, `--json`, `--diff`, the explorer card, four `[families]` keys in `.fux/inspect.toml` under [L12](../../records/0013_LAW-12-values-live-in-config.md), the tests and SR-INSPECT decision 24 have landed. **Open: DoD 11** — the golden seed needs families and planted misfits, and a filed rung must report the lens, before `misfit_floor` is anything but PROVISIONAL. That is golden-adjacent work and waits until W-230's live probe shows the traversal guard firing.

**Model:** Claude Code, Sonnet for the lens and its tests; Opus only if the
skeleton-distance design in §3 turns out to need a compare doc.

## §1 — The ask, and the ruling that places it

Arpit, 2026-09-27 (Cowork): *"can we build out a tool which can do pattern
recognition … of the documents that are being ingested, maybe in grouping …
how one document looks like, or how a bunch of documents look like … a CLI
that is available, which can be ingested by Claude Code, and can give
meaningful answers."*

Placed, same session, on two standing rulings:
- *"all of the index X-ray lives inside `fux inspect` — no new verb"* (Arpit,
  2026-09-23, W-220). This is a **lens**, not a tool.
- the top-10 test (Arpit, 2026-09-22): a per-document tool is judged by whether
  it helps an agent reach the best ten documents, not by how much it shows.

**What it is for.** Three things, honestly ranked:
1. **Orientation** — an agent can ask *"what kinds of documents does this
   corpus hold?"* and get a short deterministic answer. Nothing answers that
   today.
2. **Quality** — a document that breaks its family's shape (an ADR with no
   *Decision* section; a runbook with no steps) is named, with the lever.
3. **Boilerplate discovery** — a family's shared headings are the stopword and
   `.fuxignore` candidates `inspect`'s boilerplate lens finds by df; this lens
   finds them by *shape*, which catches template words below the df floor.

**What it is NOT for.** Ranking. No prior, no re-weighting, no change to `ask`.
A family → intent prior is W-168 step 9's business and stays there.

## §2 — What already exists (do not rebuild)

[`src/fux/inspect/lenses.py`](../../src/fux/inspect/lenses.py) `duplication()`:
- minhash (64 perms, 16 bands × 4) → candidate pairs → **exact** Jaccard ≥
  `NEAR_DUPLICATE_JACCARD` — near-duplicates.
- **exact heading-SET signature** → `families` — two docs are one family only
  when their sorted heading tuples are byte-equal.

The second is the seed of this item and its limit: an ADR whose author added
one extra `## Notes` heading is a *different* family today. **This item
generalises exact-set families to near families, and adds misfits.** The
near-duplicate half is untouched.

Also existing and reused unchanged: `graph_shape()` communities (linkage, not
shape — a different grouping, reported beside, never merged), the
`.fux/runtime/inspect/dictionary.json` word dictionary (SR-INSPECT decision 3),
the Index tab's lazy-per-lens rendering (W-220).

## §3 — Definition of done

1. **A `families` lens** in `lenses.py`, run by `inspect.run()` after
   `duplication`, reading only the committed index + the local dictionary
   (SR-INSPECT decisions 2–3). Per document, a **shape** = (a) the ordered
   heading skeleton with numerals and dates masked, (b) the frontmatter key set,
   (c) a length bucket. Family assignment is **agglomerative, single pass,
   complete-linkage over skeleton Jaccard**, threshold from `inspect.toml`,
   ties broken by doc id — a function of the corpus and nothing else (L3).
   No k, no seed, no random restart.
2. **Each family is named** by its shared skeleton (first four headings, as the
   exact-set families are today) and carries: member count, the folder(s) it
   lives in, its shared frontmatter keys, its length band.
3. **Misfits.** For each family, members whose skeleton is missing a heading
   ≥ `family_core_share` of the family carries — reported worst-first with the
   missing heading named. A document in no family of size ≥ 2 is a
   **singleton**, listed but not flagged.
4. **Two numbers, one flag.** `families_share` (docs in a family of ≥ 2) is
   descriptive. `misfit_share` carries a flag at a **PROVISIONAL** floor,
   marked as such, measured on golden before it is tuned — the same discipline
   as `SEPARATION_FLOOR`.
5. **One lever per finding**, from `LEVERS` and nothing new: a misfit →
   *fix the source*; a family's shared headings → the existing boilerplate
   levers; a family split across folders → `.fuxignore` / `archived=`.
6. **`--json`** carries the lens under `families`; the prose report has a
   section; **`--diff`** reports families gained/lost/renamed between two
   reports.
7. **Explorer Index tab** gains a *Families* card, computed by the server
   through `fux.inspect` like every other lens (SR-SERVE d5 as amended by
   W-220) — the page computes nothing. A family click lists its members; a
   member click opens the Documents tab. **The card is not optional:**
   W-229's parity test ([SR-SERVE](../../records/0158_serve.md) decision 16) fails a lens the
   explorer does not render, so this lens lands after W-229 and against it
   (Arpit, 2026-09-28: *"everything in inspect should be present in serve"*).
8. **Every threshold** — the skeleton-Jaccard cut, `family_core_share`, the
   misfit floor, the length-bucket edges — lives in `.fux/inspect.toml` and
   nowhere else (L12). `fux doctor --fix` writes them from the template.
9. **Tests**: a planted corpus with three families, one misfit per family, one
   singleton, and one exact-set family that must survive unchanged; a
   determinism test (shuffled ingest order → byte-equal report); the L12 AST
   test passes with no new allow-list line.
10. **Records**: SR-INSPECT gains the lens as a numbered decision and its
    Reference block cites §5 below; `fux-inspect` and `fux-serve` skills gain
    one paragraph each; `CHANGELOG.md`; `IMPLEMENTATION.md`.
11. **Measured, not asserted.** Before the flag's floor is anything but
    PROVISIONAL: the golden seed corpus must *contain* families and planted
    misfits (SR-WORK-TESTDATA — the feature's input must exist in the data,
    ADR-RS decision 23), and one rung filed under `work/regression/` reports
    the lens's numbers on it.

## §4 — Forks, with the default taken

| fork | default | why |
|---|---|---|
| skeleton = heading **set** or **sequence**? | ordered sequence for the shape; **set** Jaccard for the distance | order is part of a template's identity, but a filled-in template reorders sections and is still the template (today's comment, kept) |
| distance = Jaccard over headings, or over headings + body terms? | headings + frontmatter keys only | body terms make it topic clustering, which is `graph_shape`'s job and a different grouping |
| linkage | complete | single-linkage chains unrelated shapes through one bridge doc; average needs a tie rule Jaccard does not give cheaply |
| embeddings / a local model for header similarity (as arXiv 2402.13906 does) | **no** | L3 keeps models out of anything that produces a committed byte; this lens commits nothing, but a deterministic lens that a golden rung can reproduce byte-for-byte is the point of `inspect` |

Arpit overrules any row by editing this table; a builder does not.

## §5 — Reference

- Broder, *On the resemblance and containment of documents*, 1997 — the minhash
  the existing lens already implements.
- Manku, Jain, Sarma, *Detecting near-duplicates for web crawling*, WWW 2007 —
  SimHash; considered, not taken (minhash is already in the tree).
- [Collection-wide similarities for unsupervised document structure extraction](https://arxiv.org/html/2402.13906v2),
  2024 — headers → similarity graph → communities → the corpus's typical
  structure. The closest published shape to this lens; it uses embeddings and
  Louvain, both replaced here (§4).
- [Unsupervised document and template clustering using multimodal embeddings](https://arxiv.org/html/2506.12116v2),
  2025 — template-level ARI up to 1.0 on FATURA **with no non-neural baseline
  reported**. The gap this lens measures into.
- [`src/fux/inspect/lenses.py`](../../src/fux/inspect/lenses.py) `duplication()`
  — the exact-set families this item generalises.
- Related, not folded: `work/proposals/code-pattern-recognition.md`
  — the code half of the same ask, parked as a proposal.

## §6 — Hazards

- 🔴 **Do not touch `src/fux/inspect/` while the Words session holds it** (see
  `NOW.md`); W-225 4c goes first for the same reason.
- A heading skeleton over a `ctx`-heavy decoded document (spreadsheet rows,
  chat logs) is empty; such docs are singletons by construction and the report
  must say *no headings* rather than *unique shape*.
- The exact-set `families` output is consumed by `--diff` and the Index tab
  today; keep its field name and shape byte-identical.
