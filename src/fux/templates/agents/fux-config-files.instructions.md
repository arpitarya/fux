---
applyTo: "fux.toml,.fux/tune.toml,.fux/output.toml"
---

# Editing Fux configuration

`fux.toml`, `.fux/tune.toml` and `.fux/output.toml` are committed: an edit
changes ranking or output for everyone.

- **Only when a human asked for that change.**
- **Never redirect `fux tune` or `fux output` over an existing file** - they
  print engine defaults and would erase this repo's choices.
- **Ranking and index-limit keys belong in `.fux/tune.toml`**; an unknown key in
  `fux.toml` is silently ignored.
- **Judge a tuning change per query, by rank**, against expectations written
  down before the edit - never by one query or an average score.
- **`[index]` in tune.toml re-extracts the whole committed index.**
- Check both with `fux doctor --json` - the `fux.toml loads` and
  `tune.toml loads` rows. Restart `fux mcp` after editing `[mcp]`.

Full procedure: the `fux-config` skill.
