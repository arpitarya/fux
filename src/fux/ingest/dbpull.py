"""`fux db pull <url>` — fetch a CI-built index, verified against fux.lock.

Re-crawling a 100k-page corpus on every laptop is not a plan. CI builds the
index once and publishes it; everyone else pulls that artifact.

Two rules make this safe enough to be worth having:

- **Verified, not trusted.** The artifact's sha256 must match what `fux.lock`
  records. A wrong index is worse than no index, because it answers
  confidently — so a mismatch refuses rather than warns.
- **Explicit.** This lives inside the ingest fence with the crawler. It is a
  user action, never something a query can trigger.

v1 is deliberately plain: a URL and an env-var auth header. S3 and OCI
registries wait for a real consumer to ask (proposal §12).
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import Config, find_root, load
from ..errors import FuxError
from ..index.sqlstore import DB_REL
from .lock import read as lock_read
from .manifest import sha256_bytes

AUTH_ENV = "FUX_DB_AUTH"
LOCK_DB_KEY = "db:index"  # the lock row recording a published artifact's sha
_TIMEOUT = 120
_CHUNK = 1 << 16


def expected_sha(config: Config) -> str | None:
    """The artifact sha `fux.lock` records, if the corpus publishes one."""
    record = lock_read(config.root).get(LOCK_DB_KEY)
    return record.get("sha256") if record else None


def fetch(url: str, *, timeout: int = _TIMEOUT) -> bytes:
    if not url.startswith(("http://", "https://")):
        raise FuxError(f"`db pull` needs an http(s) URL, got {url!r}")
    request = Request(url, headers={"User-Agent": "fux/db-pull"})
    token = os.environ.get(AUTH_ENV)
    if token:
        # Header, not a query parameter: credentials must not land in access logs.
        request.add_header("Authorization", token)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fenced, explicit
            parts, total = [], 0
            while True:
                block = response.read(_CHUNK)
                if not block:
                    break
                parts.append(block)
                total += len(block)
            return b"".join(parts)
    except HTTPError as exc:
        hint = f" (set {AUTH_ENV} if the artifact store needs credentials)" if exc.code in (
            401, 403
        ) else ""
        raise FuxError(f"db pull failed: HTTP {exc.code} {exc.reason}{hint}") from exc
    except URLError as exc:
        raise FuxError(f"db pull failed: {exc.reason}") from exc


def install(config: Config, data: bytes, *, expected: str | None) -> Path:
    """Verify then write. Nothing touches `.fux/index/` until the sha matches."""
    actual = sha256_bytes(data)
    if expected and actual != expected:
        raise FuxError(
            "sha256 mismatch — the artifact is not the corpus fux.lock describes\n"
            f"     expected {expected}  got {actual}\n"
            "     (run `fux ingest` to build locally, or ask for a rebuilt artifact)"
        )
    target = config.root / DB_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    for suffix in ("-wal", "-shm"):  # stale journals would describe the old db
        (config.root / (DB_REL + suffix)).unlink(missing_ok=True)
    return target


def cmd_db(args) -> int:
    if args.db_command != "pull":  # argparse constrains this; belt and braces
        raise FuxError(f"unknown db subcommand {args.db_command!r}")
    config = load(find_root())
    expected = expected_sha(config)
    data = fetch(args.url)
    print(f"  fetched  {len(data) / 1e6:.1f} MB")
    target = install(config, data, expected=expected)
    if expected:
        print(f"  verified sha256 {expected[:12]}… against fux.lock")
    else:
        # Say so plainly: an unverifiable artifact is a weaker guarantee, and
        # silently accepting one would misrepresent how much was checked.
        print(
            "  warning: fux.lock records no published artifact sha — "
            "installed unverified"
        )
    print(f"  wrote    {target.relative_to(config.root).as_posix()}")
    return 0
