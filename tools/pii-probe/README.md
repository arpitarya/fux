# `pii-probe` — read what a rule would remove, before you commit to it

```console
$ python3 tools/pii-probe/probe.py .              # every rule
$ python3 tools/pii-probe/probe.py . --rule email # one rule
$ python3 tools/pii-probe/probe.py . --counts-only
```

## Why this exists

`fux doctor` compiles every pattern in `.fux/pii.toml` and names any that fail.
That catches a **broken** rule. It cannot catch the failure that actually
bites: a rule that is well-formed and **too broad**.

Redaction is irreversible in the index. A rule matching one word too many
removes real vocabulary, documents stop being findable by the terms that would
have found them, and — unlike a refusal, which produces a skip a human reads —
**nothing anywhere looks wrong**. The index is simply a little worse, forever.

So the workflow for adding a rule is: write it, probe it, read the matches,
*then* enable it.

## Two things worth reading in the output

- **A rule that never fires.** It is not protecting you; it is a rule someone
  will trust. Either the pattern is wrong or the risk is not in this corpus.
- **A rule firing far more often than the corpus can explain.** Usually it is
  matching text an earlier rule inserted — rules run top to bottom and a
  replacement is ordinary text to the rules below it.

⚠ **The output contains the values it found**, because you cannot judge a rule
without seeing what it caught. Treat it as being as sensitive as the corpus.
`--counts-only` gives you the shape without the values.
