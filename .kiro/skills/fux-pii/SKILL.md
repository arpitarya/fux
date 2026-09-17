---
name: fux-pii
description: Understand and diagnose Fux PII redaction in .fux/pii.toml — why fux stops when the file is missing, rule syntax (regex, group, luhn/verhoeff), redaction versus refusal, probing a rule for false positives, and what redaction does not cover. Use for "pii.toml missing", "false positive on a phone or card number", "add a PII rule for employee IDs", "why can't fux find this number". Write rules ONLY when explicitly asked.
---

# PII redaction in Fux

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

> ⚠ **`.fux/pii.toml` is committed policy.** A rule change decides which values
> ship inside the index every teammate clones. Explaining and probing are always
> fine; add, loosen, enable or delete a rule only when a human asked for it.
>
> ⚠ **Never put a real identifier into a rule, a test, a fixture, a commit
> message or a chat reply.** Use obviously fake values:
> `jane.doe@example.com`, `AKIAIOSFODNN7EXAMPLE`, `4111 1111 1111 1111`.

---

## 1 · What it does — redaction, never refusal

**A matching value is replaced in the text before extraction; the document is
still indexed.** Nothing is skipped for PII.

| plane | PII | why |
|---|---|---|
| `.fux/index/` | **redacted** (`[PII:<rule>]`) | committed, cloned by everyone |
| `.fux/acquired/` | raw | gitignored; must stay the bytes the source returned |
| `fux answer` quotes | raw | read from the source under the reader's own access |
| `.fux/runtime/pii-counts.json` | counts only | gitignored; what the last ingest redacted |

- **So `fux answer` can quote a value that `fux find` cannot find.** That is the
  design, not a failed redaction.
- **The record's sha is taken from the raw bytes**, so citations still verify
  `current` against an unchanged source.
- ⚠ **`fux ingest --list-skipped` never mentions PII** — redaction skips nothing.

---

## 2 · The file is required

| situation | what you see | do |
|---|---|---|
| file missing | every verb except `setup`, `tune`, `output`, `doctor` exits `1` with `error: .fux/pii.toml is missing, and fux will not run without it …` | tell the human; `fux setup` writes the starter and keeps every existing file |
| file present, rules all commented | loads, redacts nothing; `doctor --json` row `pii rules` has `ok: true`, `level: "warn"` | a deliberate choice — leave it |
| a rule is malformed | `fux ingest` exits `1` naming the rule; `doctor` row `pii rules` has `ok: false` | fix the rule the message names |

⚠ **`fux setup` enables the starter's safe rules.** The next `fux ingest`
re-extracts every document and removes their matches from the committed index.
Say that before running it.

⚠ **Never delete or empty the file to get past an error.** A missing file is an
accident fux refuses on purpose; an empty one is a policy someone must choose.

---

## 3 · Rule syntax

```toml
[[rule]]
name        = "employee-id"               # required, unique
pattern     = '''\bEMP-([0-9]{6})\b'''    # required; Python regex, literal ''' string keeps backslashes
replacement = "[PII:employee-id]"         # optional; default "[PII:<name>]"
flags       = ["ignorecase"]              # optional: ignorecase | multiline | dotall | verbose
group       = 1                           # optional; replace only this capture group, keep the rest
validate    = "luhn"                      # optional: luhn | verhoeff
```

**Refused at load, with the rule named:** a pattern that can match the empty
string, an unknown key, flag or validator, a `group` larger than the pattern's
capture groups, a duplicate `name`, and any top-level key other than `[[rule]]`.

- **Rules run top to bottom, each a full pass.** A later rule can match text an
  earlier one inserted — put narrow rules before broad ones.
- **`validate` checks the ASCII digits of the target** — the `group`, or the
  whole match at `group = 0` — separators ignored. A shape match that fails the
  checksum **stays in the index**.
- ⚠ **A checksum is a 1-in-10 filter, not proof.** One random digit run in ten
  passes Luhn or Verhoeff.
- ⚠ **With `validate` and `group = 0`, a pattern that swallows a digit of
  context fails every checksum** and silently redacts nothing. Capture the value
  in a group.
- **Keep `replacement` stable** — it is committed; changing it rewrites every
  affected record.
- **There is no allowlist key.** Express an exception in the pattern:
  anchors, required separators, lookarounds, a narrower shape, `validate`.

**The starter** enables `email`, `jwt`, `aws-access-key`, `github-token`,
`bearer-token`, `pan`, `us-ssn`, `us-itin`, `us-mbi`, `ca-sin`. It ships
`aadhaar`, `card`, `phone-in`, `phone-nanp`, `private-ip`, `us-ein`,
`ca-postal-code` **commented out**, each with a note on what it over-matches —
read that note before enabling one.

---

## 4 · Probe a rule before it touches the index

**Rule: read what a rule catches before it goes live.** An over-broad rule
removes real vocabulary and nothing looks wrong — documents just stop being
findable by the words that found them.

Put candidate rules in a scratch TOML file **outside the repo**, save this as a
scratch script, and run it with the interpreter fux is installed in (e.g.
`uv run python` or `./.venv/bin/python`) from the repo root:

```python
# usage: python probe.py RULES.toml [PATH_PREFIX]   -- git-tracked files only
import hashlib, pathlib, subprocess, sys, tomllib
from fux.ingest import pii

rules = pii.parse(tomllib.loads(pathlib.Path(sys.argv[1]).read_text()), origin=sys.argv[1])
files = subprocess.run(["git", "ls-files", *sys.argv[2:]], capture_output=True, text=True).stdout.splitlines()
for rule in rules:
    hit = kept = 0
    for f in files:
        try:
            text = pathlib.Path(f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in rule.compiled().finditer(text):
            ok = rule.accepts(m)
            hit, kept = hit + ok, kept + (not ok)
            digest = hashlib.sha256(m.group(0).encode()).hexdigest()[:8]  # never the value itself
            print(f"{'REDACT' if ok else 'keep  '} {rule.name} {f}:{text.count(chr(10), 0, m.start()) + 1} len={len(m.group(0))} sha={digest}")
    print(f"== {rule.name}: {hit} redacted, {kept} matched the shape but failed validate")
```

It uses fux's own parser and `accepts()`, so a rule it loads is a rule ingest
loads, and `keep` lines are exactly the matches `validate` spares. It reads
plain-text files only — PDFs and Office files are not decoded.

**It prints a location, a length and a short hash — never the matched text**, so
running it does not pull a real value into your context. To judge a match, open
that line yourself only if the human agrees, and never quote it back.

---

## 5 · Adding a rule, when asked

1. **Probe it** (section 4) and read every `REDACT` line. Narrow until the list
   is only what should go.
2. **Append it** to `.fux/pii.toml`, below the narrow rules it must not
   swallow.
3. **Check it loads:** `fux doctor --json` → the `pii rules` check has `ok: true`.
4. **`fux ingest`.** A changed ruleset forces a full re-extract — the summary
   line reads `0 carried forward`.
5. **Confirm:** `.fux/runtime/pii-counts.json` → `body.<rule name>` should be
   near the probe's count — the probe reads every tracked text file raw, ingest
   counts indexed document bodies only (`documents` is the denominator;
   enrichment counts are partial when `partial` is `true`).
6. **Tell the human** the rule, the count, that every document was re-extracted,
   and that `.fux/index/` changed.

---

## 6 · False positives and misses

| symptom | likely cause | fix |
|---|---|---|
| a version, ticket or order number disappeared from search | shape-only rule | require separators, anchor on context, or add `validate` |
| card-shaped order ids redacted | no checksum | `validate = "luhn"` — and still probe; 1 in 10 passes |
| phone rule eats dates and port ranges | pattern not anchored on a country code | anchor it (`\+91`, `\+1`), require separators |
| rule counts 0 but values are there | context digit inside a validated match, or wrong shape | probe — the values show as `keep`; move them into a `group` |
| a count far larger than the corpus explains | a rule matching an earlier rule's replacement, or too broad | probe; reorder or narrow |

**Fixing a rule is reversible for files:** the next `fux ingest` re-extracts
from the working tree under the new rules.

---

## 7 · What redaction does not cover

- ⚠ **A document's own PATH is never redacted** — it is the address `fux answer`
  fetches with and the key the index is sorted on, so a redacted one addresses
  nothing. **Ingest prints a note** naming the documents whose path matches a
  rule (`N document path(s) match a pii.toml rule …`); the fix is to rename the
  file or `.fuxignore` it, and neither is something fux may do for you.
- **A frontmatter `title:` IS redacted**, like the body, since 2026-09-11. On an
  index built before that, re-ingest before believing a title.
- ⚠ **URL documents are re-redacted only when their bytes are fetched again.**
  An offline `fux ingest` — `--full` included — carries URL records as they
  are, and an `update=never` URL is never re-fetched. After a rule change, run
  `fux ingest --refetch-all` and confirm.
- **Enrichment:** `fux enrich --check` refuses a file whose body matches a rule
  (`refused: … matches .fux/pii.toml rule(s): …`). Rewrite the sentence; do not
  paste a redaction into it.
- **`meta` is not redaction.** Terms are stored hashed for every document, and
  anyone who can guess a value can still search for it — only a rule removes
  it. For URL sources `meta = "hashed"` (the default) keeps titles and headings
  out of the record as readable text; `meta = "plain"` commits them readable.

**Leak check — plaintext values in the committed index:**

```bash
python probe.py .fux/pii.toml .fux/index    # any REDACT line here is a value committed in plaintext
```

---

## Don't

- **Don't write real PII** into rules, tests, fixtures, commits or chat.
- **Don't delete, empty or comment out `.fux/pii.toml`** to make an error go away.
- **Don't enable a commented starter rule without probing it** on this corpus.
- **Don't read an `answer` quote containing a value as a redaction failure.**
- **Don't look for PII in `--list-skipped`** — nothing is skipped.
- **Don't claim a rule change swept the corpus** until URL documents were
  re-fetched and the path note was read.
- **Don't add or loosen a rule as a side effect** of another task.

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-sources, fux-index, fux-maintain, fux-config, fux-mcp, fux-fetcher, fux-decoder, fux-enrich, fux-archived-results.
