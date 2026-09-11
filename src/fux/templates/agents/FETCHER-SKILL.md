---
name: fux-fetcher
description: Write or edit a Fux URL fetcher in .fux/fetchers/ (http.py, the signed-in-Chrome cdp.py, or a new one) and the sign-in/refusal rules in .fux/refusals.toml. Use ONLY when explicitly asked, e.g. "fux can't fetch our wiki", "add a fetcher for Confluence", "pages come back as the login page", "our wiki pages are being refused". Writes committed Python and policy that decide which web pages enter the index.
---

# Writing a Fux fetcher

Fux never opens a socket itself. A **fetcher** — a Python file committed in
`.fux/fetchers/` — retrieves each URL's bytes; **`.fux/refusals.toml`** names the
responses that are not the document (a sign-in page, an error shell). Fux
imports a fetcher only for `fux add <URL>`, `fux update`, and `fux answer` citing
a URL. `fux setup` writes the two shipped fetchers once; **after that they are
the repo's, and fux never rewrites them.**

> ⚠ **This skill writes committed code and policy that decide which pages are
> indexed.** Act only when a human asked. Never edit a fetcher or a refusal rule
> as a side effect of another task.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · Decide which job this is

| the ask | what to do |
|---|---|
| the page needs the user's login (SSO, SharePoint, Confluence) | `fetch=cdp` on that URL's line — §4 |
| a plain GET needs a header, proxy or token | edit `.fux/fetchers/http.py` |
| the system needs its own API (Confluence REST, Notion) | a new fetcher file, routed as in §3 |
| a sign-in page got indexed, or should be caught | a rule in `.fux/refusals.toml` — §5 |
| a real page is refused | fix or delete the rule named in `[brackets]` in the skip reason |
| the host answers 429 | `is_rate_limited` (§2) and a lower `[sources.url] max_parallel` |
| the page arrives but decodes badly | not a fetcher problem — the `fux-decoder` skill |

**Look before writing:**

```bash
ls .fux/fetchers/ && grep -n "fetcher\|max_parallel" fux.toml
fux doctor --json      # checks: "fetcher optional functions", "refusal rules", "url sources"
```

## 2 · The contract

```python
def fetch(url: str) -> tuple[bytes, str]: ...        # REQUIRED: body + Content-Type
def configure(config: dict) -> None: ...             # optional: [sources.url.config], verbatim
def connect() -> None: ...                           # optional: once, before the batch
def close() -> None: ...                             # optional: once, after — even if fetch raised
def validate(url: str) -> str | None: ...            # optional: a cheap change token
def is_rate_limited(exc: Exception) -> bool: ...     # optional: was this failure a rate limit?
MAX_PARALLEL = 1                                     # optional: absent means 1
```

| rule | why |
|---|---|
| **Return the server's bytes and its declared Content-Type, unconverted** | The type picks the decoder (HTML, PDF, JSON, CSV, XML, Office, RTF, mail); `text/markdown` and `text/plain` are used as-is. Converting here makes the index depend on which fetcher ran |
| **Raise on failure** | The URL becomes a skip, `fetch failed: <your message>`, its prior record is kept, and the batch continues. Write the message for a human |
| **`configure` or `connect` raising stops the whole run** | Reserve it for "this fetcher cannot work at all" |
| **Secrets come from the environment or a borrowed session** | The fetcher file and `fux.toml` are committed |
| **Write no files** | Retention is fux's, per URL line (`keep=`) |
| **Return the resource, not a rendering** | Nonces and timestamps change the sha on every fetch, so the page re-indexes forever |
| **Import nothing from fux** | Neither shipped fetcher does; yours keeps working when fux's internals move |
| **Never return a bare `str`** | Still accepted, for old fetchers, but read as Markdown — type-based decoding is skipped |

**`validate(url)`** — the same token as last run means the body is **not**
fetched. `None`, a raise, or a different token means fetch as normal.
It can save work and can never change a record.

**`is_rate_limited(exc)`** — `True` makes fux retry that URL 3 times with
1 s / 2 s / 4 s backoff, count it per host, and print
`note: <host> rate-limited this run N times`. Absent or `False`: no retry.
**It fails OPEN**: a predicate that raises prints one warning per run and counts
as `False`. Set a flag where you see the status code (`err.rate_limited = True`)
and read the flag; never match `"429"` in the message.

**`MAX_PARALLEL`** — fux runs `min(MAX_PARALLEL, [sources.url] max_parallel)`
fetches at once and prints a `clamped` note when the config asks for more.
Declare more than `1` only if `fetch` is safe on many threads after a single
`connect()`. The shipped `http.py` says `8`; `cdp.py` says `1`.

## 3 · Routing a URL to a fetcher

- **`fetch=` takes `http` or `cdp` and nothing else.** A name resolves to
  `<directory of [sources.url] fetcher>/<name>.py`.
- **A line with no `fetch=` uses the file `[sources.url] fetcher` names.**
- **Nothing escalates.** A GET that returns a useless shell returns it every run;
  a human changes the line.

| you want | do |
|---|---|
| every URL through a modified GET | edit `.fux/fetchers/http.py` in place |
| one URL through the browser | `fux add <URL> --cdp` — rewrites that line |
| a new `.fux/fetchers/confluence.py` | point `[sources.url] fetcher` at it, and keep `fetch=` **off** its lines |

⚠ **`fux add` writes `fetch=http` unless given `--cdp`**, which bypasses a
custom default fetcher. For the new-file route: `fux add <URL> --no-ingest`, delete `fetch=http`
from the line in `.fux/sources/urls`, then `fux update <URL>`. A later `fux add`
on that URL writes `fetch=http` back.

⚠ **`[sources.url.config]` goes to every fetcher that has URLs in the run**, and
both shipped `configure()`s raise on a key they do not know. Only
`fetcher_max_parallel` is known to both. Give a fetcher-specific setting a module
constant instead, or add the key to the other fetcher's `_SETTINGS`.

## 4 · `cdp.py` — borrowing a signed-in Chrome

**It attaches to a Chrome the user already runs and is signed in to**, so the
user's session is the credential and fux stores none.

```bash
# the user starts it — a DEDICATED profile — and signs in there
chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.fux-chrome"
fux add https://sharepoint.corp/…/Plan.xlsx --cdp
```

- 🔴 **While the port is open, any local process can drive every site that
  profile is signed in to.** Use a separate profile signed in only to the
  sources fux needs, and close Chrome when the fetch is done. Recent Chrome
  versions also refuse remote debugging on the default profile, which is the
  second reason for `--user-data-dir`.

- **Nothing listening on the port stops the run**:
  `[sources.url] fetcher connect() failed: nothing listening on http://127.0.0.1:9222 …`.
  `LAUNCH_CHROME` defaults to `False`, because a browser fux starts is signed in
  to nothing.
- **It intercepts the network response; it does not run the page's JavaScript
  into a document.** It returns what the server sent for that URL. A page whose
  text is built client-side still arrives as the app shell, and fux prints
  `note: <url> decoded to N word(s) from B bytes … application shell`. Point the
  line at the underlying file, export or API URL instead.
- **It does not treat an error status as a failure.** A 403 or 404 page comes
  back as a body, so `.fux/refusals.toml` is what keeps it out.
- **Tunables** (`[sources.url.config]`): `cdp_host`, `cdp_port`, `launch_chrome`,
  `chrome_binaries`, `extra_chrome_flags`, `load_timeout_s`,
  `fetcher_max_parallel` — mind the ⚠ in §3 if `http` lines also exist.
- ⚠ **`MAX_PARALLEL` ships at `1` on purpose.** Raise it only after a multi-URL
  run where you checked each record's content matches its URL.

## 5 · Refusals — `.fux/refusals.toml`

**Checked after `fetch`, before anything is kept or decoded.** A match is a skip
whose reason is the rule's `reason` plus `[name]`; nothing is retained, the prior
record stays, and `fux doctor` counts hits per rule.

**Underneath the rules is a check you cannot turn off:** a body declared as
PDF must start `%PDF-`, and one declared `.docx`/`.xlsx`/`.pptx`/`.odt` must
start `PK\x03\x04`.

```toml
[[rule]]
name   = "confluence-anonymous-view"          # required, unique; reported by doctor
reason = "Confluence served the anonymous view - sign in and re-run"   # required; write an instruction
content_type  = ["text/html"]                 # prefix match, parameters ignored
body_contains = ["login.action", "aui-message-warning"]   # substrings; any one matches
```

- **Conditions:** `content_type`, `requested_suffix`, `requested_suffix_not`
  (`""` means a URL with no extension), `body_contains`, `body_starts_with`
  (hex, `"50 4b 03 04"`), `max_bytes` (fires when the body is **smaller**).
- **Inside a rule, conditions AND and list items OR. The first matching rule in
  file order wins.**
- **Rules see bytes only** — no status, no redirect, no header beyond the type.
  Match what a sign-in page must carry (`type="password"`, `name="loginfmt"`,
  `name="SAMLRequest"`), not branding that a redesign rewrites.
- `body_contains` searches the first 1 MiB of a text-like body, or any body up
  to 8 KiB; a large binary body is never matched by it.

**It fails CLOSED on its own config.** No file means only the built-in check. A
malformed file, an unknown key, a rule with no conditions, a duplicate name, or
`""` inside `content_type`/`body_contains` stops the run before any fetch.

**The two suffix-based starter rules know the common wiki extensions** —
`.action`, `.aspx`, `.asp`, `.php`, `.jsp` alongside `.html`/`.htm`. A wiki
serving `viewpage.action` or `Page.aspx` is serving a document, not a sign-in
wall. **If yours uses another extension, add it to `requested_suffix_not` on
both rules** — that list is what "this URL asked for a web page" means.

⚠ **`suspiciously-small-document` still refuses any response under 1 KiB from an
extensionless URL**, which is the share-link case it exists for. A genuinely
tiny real page there is lost: raise `max_bytes` or delete the rule. **There is
no warn level** — every rule in this file refuses.

## 6 · Verify on one URL before claiming it works

**Call the fetcher directly and READ what comes back**, with the interpreter
that runs fux:

```python
import importlib.util, pathlib, tomllib
from fux.ingest import refusals
url = "https://wiki.corp/display/ENG/Runbook"
spec = importlib.util.spec_from_file_location("probe", ".fux/fetchers/http.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
config = tomllib.loads(pathlib.Path("fux.toml").read_text())["sources"]["url"].get("config", {})
getattr(mod, "configure", lambda c: None)(config)
getattr(mod, "connect", lambda: None)()
try:
    raw, ctype = mod.fetch(url)
finally:
    getattr(mod, "close", lambda: None)()
print(ctype, len(raw), raw[:300])
print("refused:", refusals.refused(refusals.load(pathlib.Path(".")), url, ctype, raw))
```

Check the type is real, the bytes are the document and `refused:` is `None`.
Then fetch signed out and confirm `refused:` names your rule.

**Then through fux, one URL:**

```bash
fux add <URL>              # exit 1 + "the line is written; the fetch failed: …" on failure
fux update <URL>           # for a listed URL; exit 0 even on failure — read the "! <url> — …" line
fux doctor --json          # "refusal rules": hits per rule, and rules that never fired
```

- ⚠ **`fux add --dry-run` never fetches.** It proves nothing about a fetcher.
- ⚠ **`fux answer` verifies a URL citation by fetching it again and decoding it
  the same way ingest did.** A citation that reports `as-ingested` or
  `unverified` while the fetcher works means the verify fetch failed, returned
  no bytes, or returned a type no decoder claims — `--audit` names which. **Do
  not switch `fetch` to returning `str`**: prose is the pre-2026-08-26 ramp, and
  returning it throws away the content type the decoder plane needs.

**When you finish:** say which files changed and which URLs now route or refuse
differently; `fux update --all` re-fetches every URL under the new code.

## Don't

- **Don't put a token, password or cookie in a fetcher, `fux.toml` or `[sources.url.config]`.**
- **Don't convert HTML to Markdown inside `fetch`** — return bytes and the type.
- **Don't expect `cdp.py` to render JavaScript**, and don't raise its `MAX_PARALLEL` unverified.
- **Don't detect a rate limit from exception text** — set and read a flag.
- **Don't delete a refusal rule to make a page appear** — find out why it matched.
- **Don't add a key to `[sources.url.config]`** that another fetcher in use will reject.
- **Don't write a rule from a guess** — write it from a captured response.

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-sources, fux-index, fux-maintain, fux-config, fux-mcp, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
