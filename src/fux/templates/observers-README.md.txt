# `.fux/observers/` — tell your analytics what fux did, never what it read

Drop a `*.py` file here with one function:

```python
def observe(record: dict) -> None:
    ...  # append `record` somewhere; the return value is discarded
```

After a fux verb has **fully rendered** — stdout flushed, exit code fixed —
every file here is called once, in sorted filename order, with one record:

    verb · args_hash · band · answerable · n_results · n_related
    refer_verdicts · ms · expand_used · q_arms · fux_version

## What is NOT in it, and will not be

The question. Any `--expand` text. A document id, a path, a snippet, the
answer. Every value is a count, a boolean, a fixed name, or a hash — so this
hook can tell you how fux is being used and can never tell you what anyone
looked for. `args_hash` excludes the question too: it is a hash of the
normalised FLAGS, so you can join a run to a command without fingerprinting
the query.

## What it cannot do

Change anything. There is no return path, the record is a copy, and the
dispatch runs after every write the verb makes. An observer that raises is
skipped for that run; one that is slow is abandoned at `[observe] max_ms` in
`fux.toml`. Your analytics cannot make `fux ask` wrong, and cannot make it
slow.

`fux doctor` lists the files here and whether each one fired on the last run.
