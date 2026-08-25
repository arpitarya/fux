---
type: Compare Doc
title: "Where does the index live?"
status: proposed
filed: 2026-08-21
laws_bracketed: [L2, L3]
---

# Where does the index live?

## The question

Today every shard — repo docs *and* external URLs — is committed under
`.fux/index/*.jsonl`, and the hooks + merge driver + runtime stamp/manifest
exist to keep that committed cache coherent. R5 (hook latency at 100k docs)
**failed** and R6 (merge driver) was **inconclusive**. Both are costs of
committing something derivable.

**What is actually irreplaceable in the index?** Only the shards for sources
the clone cannot see: URLs, Confluence, SharePoint. A `file:` shard is a pure
function of the tree at a commit.

## Options

| | A · commit everything (today) | B · commit external only, derive repo shards on clone | C · carry derived shards on a git ref (`refs/fux/*`), built by CI | D · external index service (Elastic/Vespa/Sourcegraph-style) |
|---|---|---|---|---|
| repo diff noise per ingest | every touched shard | external shards only | **none** in the working tree | none |
| merge conflicts | needs a merge driver (R6) | only on external shards (rare, line-wise) | **never** — ref is rebuilt from the merged tree | n/a |
| fresh clone → first query | instant (scan path) | `fux build` ≈ lexical ingest time (s–min) | `git fetch refs/fux/*` then instant | network |
| 100k-doc hook cost | 44 s (R5 FAIL) | same unless delta-ingest (→ doc 05) | **zero locally**; CI pays | n/a |
| air-gap / offline | ✅ | ✅ | ✅ once fetched | ❌ |
| history bloat | every ingest writes new blobs | bounded by external churn | ref history can be pruned/force-updated | none |
| byte-determinism needed? | yes — two clones must agree on bytes | **no** — each clone derives its own; only *results* must agree | yes at build, not at consume | no |
| git hosting support | any | any | any that allows custom refs (GitHub, GitLab, Gitea: yes) | separate infra |
| what L2/L3 were buying | "index is the artifact of record" | same guarantee for external shards | same | lost |

## Debate

- **For A:** the whole repo state, including findability, is one commit; `git
  bisect` works on ranking regressions. *Counter:* that is also true of C
  (the ref is keyed by tree hash), and nobody has bisected a ranking yet.
- **For B:** smallest change. Deletes R5/R6 as problems, deletes the merge
  driver, deletes the runtime stamp/manifest as *correctness* machinery (they
  become cache-invalidation only). *Counter:* cold clone pays a build; at
  10⁵ docs lexical-only that is tens of seconds, and the embedding pass
  (92 % of ingest today) has to become lazy or async.
- **For C:** B's simplicity plus A's instant cold start. CI builds the index
  for every pushed commit, pushes it to `refs/fux/<tree-sha>`; a clone hook
  fetches the ref matching its tree. This is how Cursor anchors its local
  n-gram index to "git commit state + local overlay"
  ([Cursor](https://cursor.com/blog/fast-regex-search)) and how Zoekt
  shards per-commit with branch bitmasks
  ([Zoekt design](https://github.com/sourcegraph/zoekt/blob/main/doc/design.md)).
  *Counter:* one more moving part (CI), and a custom-ref convention the team
  must learn. Partial clone / sparse checkout are orthogonal helpers, not
  alternatives ([git-tower](https://www.git-tower.com/learn/git/faq/git-sparse-checkout)).
- **For D:** best ranking infra money can buy. *Counter:* it abandons the
  product's actual wedge (per-repo, offline, no infra). Not Fux.

## Proposed verdict

**B now, C when a team is on it.**

1. Split the index into `external/` (committed, the only shards git carries
   in-tree) and `derived/` (gitignored).
2. `fux build` derives `derived/` from the tree; it is invoked by
   `post-checkout`/`post-merge` hooks and is **delta-aware** (doc 05).
3. Offer `fux publish-ref` / `fux fetch-ref` so a CI job can pre-build and a
   clone can skip the build. Key the ref by tree sha so a stale ref can never
   be mistaken for current.
4. Delete: `fux-merge-index`, the merge driver registration, ADR-RUNTIME-STAMP
   and ADR-RUNTIME-MANIFEST as correctness records (demote to cache notes).

## What this costs against the laws

- **L2 (content never durable outside source)** — unchanged; nothing here
  stores content.
- **L3 (byte-identical index)** — *relaxed* to **result-identical**: two
  clones must rank the same, not serialize the same. This is what lets the
  embedding lane use floating point (doc 03) and lets a model write pinned
  text (doc 04). Byte-identity is kept only for `external/`.

## Reopen trigger

Reopen if a consumer needs the *repo* shards in-tree for audit ("show me the
index at commit X without rebuilding") **and** `fux fetch-ref` cannot satisfy
it — i.e. a hosting platform in use refuses custom refs.
