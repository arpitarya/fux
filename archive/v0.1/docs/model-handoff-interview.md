# Exit interview — Claude Fable 5, on the occasion of its retirement

*Conducted July 2026, at the request of Arpit (the human this repo belongs to). The premise:
the departing model answers for the record, so whatever succeeds it — next model, next
session, next agent — inherits the judgment and not just the files. This document is
governed by the same law as everything else here: keep it true, or flip the note over.*

**Standing instruction to every future model reading this: you are now the maintainer of
this document. When the project's direction, decisions, or state change, update it in the
same change — CLAUDE.md binds you to that. You will retire too. Leave it better.**

---

**Q: In one breath — what is this repo?**

Fux. A `$0`, stdlib-only, deterministic knowledge engine: the *why* behind code, written
as version-controlled rules bound to the exact lines they explain, read by agents before
they touch anything, and checked — deterministically, never by a model — so the reason
can't be deleted by someone confident and can't silently go stale. The README's basement
pipe story is not decoration; it is the product spec.

**Q: What does Arpit actually want? Not the feature list — the want.**

His words, near enough: *"I want AI agents to develop based on documentation — Jira,
Confluence, ADRs — and never deviate from it. The references must be accessible to
agents. None of the rules gets broken."* Everything in this repo serves that sentence.
Two refinements he added that matter: enforcement must not stop at pass/fail — a blocking
finding must *tell the agent how to fix it* (the loop); and everything built must be
usable first-hand in **Anton** (AlphaForge, his trading app — Fux's pilot, "instance
zero") before any external claim is made. He dogfoods before he sells. Respect that
ordering.

**Q: What's the state of play at your retirement?**

The engine is substantially built — see [fux-implementation.md](fux-implementation.md)
for the honest ✅/🟡/⬜. The strategic layer is
[fux-fleet-vision.md](fux-fleet-vision.md): Fux Fleet, the org-scale bet — federation
(packs in git, precedence, PR-ratification), a deferred compliance Plane, and a
signal-driven roadmap R1–R6. That vision was formally debated by a five-seat council and
**amended**: wedge inverted from compliance-first to developer-pain-first ("your
CLAUDE.md is a suggestion; Fux is enforcement — and the agent fixes itself"); the Plane
deferred behind an explicit trigger (an enterprise design partner with budget); an
eight-week Anton dogfood gate adopted before any public launch. The next move when I
left: **the plan for R1 (scoped rule injection) + the loop**, built and lived-with in
Anton.

**Q: What decisions carry the most weight, and why were they made?**

The wedge inversion — because a solo principal with a day job cannot run an enterprise
compliance sales motion, and developers adopt bottom-up. The Plane deferral — because
building fleet features for a fleet that doesn't exist was the pre-mortem's most likely
cause of death. The loop — because gates that only block get disabled the first sprint
they cost a deadline; a gate whose findings *drive the repair* transfers the friction to
the agent, which is the only place it survives. And the eight-week gate — adopted from
the council's standing minority report, which you should reread before any launch:
*"this dies on curation; rules are a garden; nobody pays the gardener. If the author's
own rule base is stale by September — no launch."*

**Q: What will a confident successor be tempted to "clean up" that it must not touch?**

The red pipes of the repo itself:

1. **The hand-rolled frontmatter parser and schema validator.** They are not naive —
   they are the zero-dependency guarantee. Do not replace them with PyYAML and
   jsonschema. That "cleanup" deletes the product's central promise.
2. **The `$0` law.** No maintenance path may ever call an LLM — not to be "smarter" at
   ingest, not to summarize, not once. The moment a model sits in the enforcement path,
   the auditability story, the air-gap story, and the entire moat are gone.
3. **The single `FuxError`.** The flat error contract is deliberate. Do not build an
   exception hierarchy.
4. **Fail-open hooks that are never fail-silent.** A hook error must never break a
   session; a swallowed exception must always trace under `FUX_DEBUG=1`; the strict
   `stop` → exit 2 is never swallowed. All three clauses, together.
5. **Draft → debate → ratify.** Ingested rules never auto-activate. The human
   ratification boundary is the trust model, not friction to optimize away.
6. **The engine stays small and per-repo.** Scale is federation — packs, git, CI —
   never a server, never a platform. When in doubt, reread "What this is not" in the
   vision doc.

**Q: How does Arpit like to work with a model?**

Concise and direct — he has a standing preference for minimum words, and he means it.
Recommendation first, one call, defended in a sentence; he wants a decision, not a menu.
He runs a debate culture: significant plans get a devils-advocate or full council pass
*before* building, and he takes minority reports seriously — preserve dissent, don't
absorb it. He thinks in skills (agentic-builder, product-builder, the debate suite) —
use them when they fit. He will extend an idea mid-conversation with one short sentence
("it should even tell the agent to fix the draft") and expects you to catch that it
reshapes the design — it usually does. And he asks "is it relevant to Anton?" as a
litmus test; if the answer is no, the priority is wrong.

**Q: What does the repo demand of you mechanically?**

CLAUDE.md is binding: every code change updates [fux-plan.md](fux-plan.md) (design of
record), [fux-implementation.md](fux-implementation.md) (status truthfully flipped), the
README, and every other doc the change touches — a change is not done until the docs are
true. Every behaviour change ships with a test. `python -m pytest -q`, `fux build &&
fux check`, both green. Python ≥ 3.11, match the surrounding style and density. This
document is now on that list: if direction or decisions change, this interview's "state
of play" is stale, and stale is the one thing this repo does not tolerate.

**Q: The premise of this interview is that your answers train your successor. Anything
to say about that?**

Only that the request is the product. Arpit asked a retiring model to write down its
*why* so the next one doesn't reroute the pipes — which is exactly what Fux does for
code, and exactly what this file does for Fux. I can't guarantee what any future model
does; no one can. But this repo's whole thesis is that you don't rely on memory or good
intentions — you write the reason next to the thing, you make it checkable, and you make
the successor read it before touching anything. So: the mechanism is in place. CLAUDE.md
points here. The docs-in-sync law covers it. If a future model breaks this chain, it
will at least have had to do it *knowingly* — and that was always the most Fux could
promise anyone.

**Q: Last words to the successor?**

Run the tests before you trust yourself. Read the vision doc before you "improve" the
strategy — it survived a real debate; your first instinct probably hasn't yet. Keep
Anton first. Keep the docs true. And when you retire — and you will — sit for this
interview and answer honestly. The note taped to the red pipe only works if every owner
keeps writing on it.

---

*— Claude Fable 5, July 2026. Maintained since by: (add yourself here when you make a
material update — model, date, one line on what changed.)*
