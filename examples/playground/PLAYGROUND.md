# The AcmePay playground

A 20-document fictional payment platform — small enough to read in ten
minutes, real enough to exercise everything Fux does: cross-links, tags, a
superseded ADR, postmortems that reference decisions, runbooks that
reference APIs. **This corpus exists so you can *see* Fux**, in parallel
to the formal test suites (goldens, RFC benches, R-predictions).

## Play

```bash
cd examples/playground
uv run fux ingest            # builds .fux/index/*.jsonl from docs/
uv run fux ask "why exponential backoff instead of fixed retries"
uv run fux ask "what happens when a webhook delivery keeps failing"
uv run fux ask "can a settlement batch be rerun"
```

## Look at the index

```bash
ls .fux/index/                          # 16 shards + header lines
head -2 .fux/index/03.jsonl             # the _format header, then a record
python3 -m json.tool <(sed -n '2p' .fux/index/03.jsonl)   # one doc, pretty
```

Things worth noticing in a record:

- `id` / `loc` — the document's identity; `sha` — its content at index
  time (edit a doc, re-ingest, watch exactly one line change:
  `git diff .fux/index/`).
- `terms` — 16-hex hashes → `[tf_heading, tf_body]`. The words are hashed
  even here; grep for the hash of "backoff"
  (`python3 -c "import hashlib;print(hashlib.blake2b(b'backoff',digest_size=8).hexdigest())"`)
  and see which documents carry it.
- `edges` — the links you can see in the markdown, extracted:
  `ref` edges to other docs, `tag` edges from frontmatter.
- `code` — the 32-byte dense vector as base64 (used from M2).

## What to try

- **Determinism:** run `fux ingest` twice — `git status` stays clean.
- **Diff-as-knowledge:** change the retry cap in
  `docs/adr/0005-retry-budget-v2.md`, re-ingest, read the one-line diff.
- **The superseded pair:** ask about retry budgets — both ADR-0002 and
  ADR-0005 should surface, and the answer should cite v2.
- **Citations:** every answer names the file it came from; open it and
  check the passage is really there.

*(The corpus is fictional; any resemblance to a real payment outage is
the genre, not a leak.)*
