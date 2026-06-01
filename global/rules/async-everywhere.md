---
id: async-everywhere
domain: code-quality
type: convention
status: active
created: 2026-06-01
updated: 2026-06-01
aliases: [asyncio, non-blocking, coroutine]
keywords: [await, event-loop, io, concurrency, python]
---
**Convention:** In async services, I/O-bound code is `async` end-to-end — no
blocking calls on the event loop, no mixing sync DB/HTTP clients into an async
request path.

**Why:** A single blocking call stalls the whole event loop, silently
serialising what should be concurrent and erasing the reason for choosing an
async stack. Consistency ("async everywhere") removes the foot-gun of an
accidental sync island.

**How to apply:** Use async clients (async DB driver, `httpx.AsyncClient`);
offload unavoidable CPU/blocking work to a thread/process pool. This is a
language-specific best practice — opt out via project config in non-async stacks.
