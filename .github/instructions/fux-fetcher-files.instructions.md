---
applyTo: ".fux/fetchers/**,.fux/refusals.toml"
---

# Editing a Fux fetcher or refusal rule

These files decide which web pages enter the index. They are committed.

- **Only when a human asked.** Never as a side effect of another task.
- **`fetch(url) -> (bytes, content_type)`**: the server's bytes and declared
  type, unconverted. Raise on failure.
- **No token, cookie or password** in a fetcher, `fux.toml` or
  `[sources.url.config]` - use the environment or a borrowed session.
- **A malformed `refusals.toml` stops the run**; a raising `is_rate_limited`
  counts as "not rate-limited".
- **Write a refusal rule from a captured response**, matching what a sign-in
  page must carry, not branding.
- `fux add --dry-run` never fetches: test on one real URL.

Full procedure: the `fux-fetcher` skill.
