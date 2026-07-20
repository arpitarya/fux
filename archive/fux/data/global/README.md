# Fux — global best-practices layer

This directory is the **global rules layer** (plan §5). It is its own git repo
(`global-rules-home.compare.md` verdict B: *git in place*): versioned, syncable
across machines via a private remote, and PR-reviewable — while always resolving
to the single path the engine reads, `~/.claude/fux/global/`.

Every project that runs `fux init` with `use_global = true` inherits these rules.
Edit a best practice **here, once**, and every linked project picks it up on its
next `fux build` / SessionStart.

## Layout

```
global/
└── rules/*.md     # cross-project conventions (files ≤100 lines, no secrets, …)
```

## Precedence

`project` overrides `pack` overrides `global` by rule `id`. `fux check` flags a
project rule that shadows or `contradicts:` a global one instead of letting it
silently win.

## Secret hygiene

Global rules sync widely — **never** put a secret in this repo. The
`no-secrets-in-vcs` rule here is also a `fux check` lint target.

## Maintained entries

| id | type | what |
|----|------|------|
| `files-max-100-lines` | convention | ≤100 lines/file (≤50 for utils) |
| `no-secrets-in-vcs` | convention | no `.env`/keys in version control |
| `doc-per-code-change` | convention | knowledge update ships with the code change |
| `async-everywhere` | convention | no blocking calls on the event loop |
