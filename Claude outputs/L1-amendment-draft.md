# DRAFT — L1 amendment: `$0`/stdlib-only → `$0`/FOSS-only, stdlib core, extras opt-in

**Status: DRAFT. Nothing has been written to the repo.** Read, mark up, then say apply.

**Ruling being recorded (Arpit, 2026-09-06, Cowork):**

> *"I want to remove the law STD lib dollar zero."* → narrowed on questioning to:
> optional extras only; *"using libraries like pandas and numpy is going to be
> helpful. I still don't want to pay for… only open source and free ones."*

---

## 0. What you are actually changing (one screen)

| clause | today | **after** |
|---|---|---|
| paid dependencies | implicitly barred by `$0` | **explicitly barred — FOSS-only, and now the law's first sentence** |
| default install | zero third-party deps | **unchanged — zero third-party deps** |
| core paths (rank, ingest, index, CLI) | stdlib | **unchanged — stdlib** |
| a built-in needing a library | illegal | **legal behind a declared optional extra** |
| consumer `.fux/decoders/` | may use anything | **unchanged** |
| dev / test tooling | "may use extras" | **unchanged** |
| numpy / pandas / scipy in harnesses | **banned outright** | **allowed** |

**This is not a law retirement.** L1 keeps its number, keeps both halves, and
gets *stronger* on the money clause. The number is not retired and nothing
renumbers — which was the failure mode worth avoiding.

⚠ **Three things this does NOT do.** Read §4 before you approve; two of your
stated drivers are not served by this change.

---

## 1. `CLAUDE.md` §Non-negotiable constraints — the normative text

### Before

```
- **L1** · **`$0`, stdlib-only runtime.** No third-party *runtime* dependencies. The
  frontmatter parser and every codec are hand-rolled on purpose — that is the
  zero-dependency guarantee and the product's central promise. Dev/test tooling
  may use extras; the runtime path may not. No numpy, pandas, or scipy
  anywhere, including in measurement harnesses.
```

### After

```
- **L1** · **`$0` and free software; stdlib-only core, extras opt-in.** Fux costs
  nothing to run and depends on nothing anyone has to buy: **no paid library, no
  paid service, no paid API — ever.** A dependency that is not free and
  open-source is not a candidate, whatever it does.
  **The default install stays dependency-free.** `pip install fux-engine`
  installs zero third-party runtime packages, and every core path — ingest,
  ranking, the index, the CLI, the refer plane — is stdlib. That is the
  zero-dependency guarantee and it is unchanged.
  **A third-party FOSS library is legal only behind a declared optional extra**
  (`fux-engine[pdf]`), only where a capability is otherwise unreachable or
  wrong, and never on a path the default install executes. Convenience is not a
  reason; a hand-rolled codec that works stays hand-rolled.
  **Dev, test and measurement tooling may use FOSS freely** — numpy, pandas and
  scipy included. ⚠ **Amended 2026-09-06** (Arpit); the previous form barred
  third-party runtime dependencies outright and barred numpy/pandas/scipy even
  in harnesses. [ADR-LAWS](docs/adr/0001_laws.md) decision 9 carries what the
  amendment traded away.
```

### ⚠ One clause I added that you did not ask for — delete it if you disagree

I have **not** put this in the block above. It belongs in ADR-LAWS decision 9 or
in L1 itself, your call:

> **A number that reaches a `VERDICT.md` is computed in stdlib arithmetic.**

**Why.** numpy's reductions are order- and build-dependent — different BLAS,
different platform, different sum. Your whole verdict discipline rests on a
measurement another machine can reproduce, and `CLAUDE.md` already bans floats
from the committed plane for exactly this reason. numpy for exploring a dataset
is fine. numpy computing the recall@5 that goes into a pre-registered verdict is
a reproducibility hole you will not notice until two machines disagree.

**Three ways to take it:** (a) as written above; (b) softer — *"a harness that
computes a verdict number states which library computed it"*; (c) drop it, and
accept the exposure named here.

**Note the internal contradiction this resolves.** The old L1 said *"Dev/test
tooling may use extras; the runtime path may not"* and then *"No numpy, pandas,
or scipy anywhere, including in measurement harnesses."* Those two sentences
fight. Your ruling settles it in favour of the first.

---

## 2. `docs/adr/0001_laws.md` (ADR-LAWS)

### 2a. §1 table row

```diff
-| **L1** | `$0`, stdlib-only runtime |
+| **L1** | `$0` and FOSS-only; stdlib-only core, extras opt-in |
```

⚠ **The handle must move in the same commit as `CLAUDE.md`.** Decision 4 says
so, and decision 8's ⚠ block records that this table has been stale twice in one
day — *"the worst case of the restatement hazard."* This row is the line people
scan instead of the law.

### 2b. New decision 9 — the amendment record

Append after decision 8, in decision 8's own shape (history table + what it
trades + what it does not do):

```markdown
**9. L1 was amended on 2026-09-06 (Arpit).** `$0` was strengthened into an
explicit free-and-open-source-only rule; `stdlib-only runtime` was narrowed to
`stdlib-only core, third-party FOSS behind declared optional extras`; and the
blanket ban on numpy/pandas/scipy in measurement harnesses was lifted.

**Arpit, 2026-09-06, in Cowork:** *"I believe using libraries like pandas and
numpy is going to be helpful. I still don't want to pay for… only open source
and free ones."*

| clause | before | **after** | why |
|---|---|---|---|
| paid dependencies | implied by `$0` | **explicit prohibition, first sentence** | it was the half of `$0` he actually cared about, and it was the unstated half |
| default install | zero third-party deps | **unchanged** | the promise being sold is *"`pip install` brings nothing with it"*, and that survives intact |
| core paths | stdlib | **unchanged** | ranking, ingest, index and CLI are what an auditor reads; nothing moves there |
| a built-in needing a library | illegal | **legal behind a declared extra** | the built-in/consumer split was drawn to route around a prohibition that no longer exists |
| harness tooling | numpy/pandas/scipy banned | **permitted** | the previous form contradicted its own preceding sentence |

⚠ **What this amendment does NOT do.**

1. **It does not unblock a model.** L3 forbids a model in the maintenance path
   and is untouched. Semantic chunking, embeddings, a cross-encoder reranker
   and LLM-boundary detection are blocked by L3 and by
   [ADR-RERANK](0041_rerank.md)'s cross-machine determinism refusal — never by
   L1 alone. **A later session citing this amendment as authority for a model
   is misreading it.**
2. **It does not make convenience a reason.** The test is *unreachable or
   wrong*, not *tedious*. Every hand-rolled codec that works today stays
   hand-rolled; rewriting one onto a library is not authorized by this.
3. **It does not touch the consumer seam.**
   [ADR-DECODE](0042_decode.md) decision 1's table — third-party parsing
   libraries are owned by `.fux/decoders/<name>.py` — stands. The amendment
   adds a second legal home, it does not close the first.

⚠ **The exposure, named rather than papered over.** `$0`/stdlib-only was
a **trivially auditable supply chain** — the enterprise wedge `CLAUDE.md`
names. `fux-engine[pdf]` is still auditable, but it is now auditable *by
reading a dependency tree* rather than *by there not being one*. That is a
weaker claim, and the README must stop making the stronger one. **The
mitigation is the default install, and the default install alone.**

⚠ **And nothing enforced L1 before this.** There was no test. The
prohibition was prose plus an empty `dependencies = []`. The amended law is
mechanically checkable in a way the old one was not — see the veto check
below — which is the one respect in which the repo is *safer* after the
amendment than before it.
```

### 2c. Veto-condition check #2 — the grep string breaks

```diff
 # 2. no record has grown its own copy of a law
-grep -rn 'stdlib-only runtime' docs/adr/ | grep -v '0001_laws.md'
+grep -rn 'stdlib-only core' docs/adr/ | grep -v '0001_laws.md'
 # expect: no output
```

**Add a third check** (this is the two-strikes rule earning its keep — a law
that nothing checks has now caused one amendment nobody could have caught
drifting):

```bash
# 2b. L1: the default install is dependency-free, and every extra is declared.
python - <<'PY'
import tomllib, pathlib
p = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
assert p["project"]["dependencies"] == [], p["project"]["dependencies"]
print("extras:", sorted(p["project"].get("optional-dependencies", {})))
PY
# expect: no assertion, and every extra listed is one a record names.
```

### 2d. Decision 7 — no change needed

*"L1 forbids third-party runtime dependencies and `concurrent.futures` is
stdlib"* stays true of the core. Leave it.

---

## 3. Downstream records that cite L1

### 3a. `docs/adr/0042_decode.md` (ADR-DECODE) — **the most affected record**

**(i) Alternatives bullet — supersede, do not delete.**

```diff
-- **Amending L1 to permit optional dependencies.** Rejected as unnecessary —
-  see §1's table. **L1 constrains the runtime fux ships; consumer code is not
-  that.** A later session proposing this amendment is crossing this fence.
+- **Amending L1 to permit optional dependencies.** Rejected here as
+  unnecessary — see §1's table — and **SUPERSEDED 2026-09-06** by
+  [ADR-LAWS](0001_laws.md) decision 9, which made the amendment on grounds
+  this record never weighed (build velocity and positioning, not decoding).
+  ⚠ **The rejection's reasoning was not refuted.** *"L1 constrains the
+  runtime fux ships; consumer code is not that"* is still true, and the
+  consumer seam in §1's table is still the first answer for a third-party
+  parser. What changed is that it is no longer the **only** answer.
```

**(ii) Reopen-trigger #2 — currently asserts something now false.**

```diff
 2. **A built-in decoder needs a non-stdlib import** to be correct rather than
-   merely convenient. **That would mean the built-in/consumer split is drawn in
-   the wrong place, not that L1 should move.**
+   merely convenient. ⚠ **Rewritten 2026-09-06:** this trigger read *"that
+   would mean the split is drawn in the wrong place, not that L1 should
+   move"* — and L1 has since moved (ADR-LAWS decision 9). The trigger now
+   fires on a **narrower** condition: a built-in decoder needs a non-stdlib
+   import **and** the capability cannot be reached from `.fux/decoders/`
+   either. Correctness alone no longer reopens this record; it now opens a
+   question about which extra to declare.
```

**(iii) Line ~222, the image decoder.** Add one sentence — **eligibility is not
a decision:**

```diff
 kept, hand-rolled per **L1** since Pillow is not stdlib). **The consequence
+belongs to ADR-TYPES, not here**: […]
```
becomes
```diff
 kept, hand-rolled per **L1 as it then stood** since Pillow is not stdlib).
+⚠ **Since 2026-09-06 this decoder is *eligible* for `fux-engine[images]`.**
+Eligible is not decided: the hand-rolled decoder works, and L1's amended test
+is *unreachable or wrong*, not *nicer*. Replacing it needs its own item.
 **The consequence belongs to ADR-TYPES, not here**: […]
```

**(iv) Lines 45 / 70 / 196 / 416** say *"stdlib only, L1"* of built-ins and
diagrams. **All still true today** — no built-in has taken an extra. Leave them;
they become wrong only on the first extra actually shipping, and that change
will own them.

### 3b. `docs/adr/0030_refer-plane.md` (ADR-REFER) — two rejections lose a leg

Both survive. Both must stop leaning on L1, or they read as ungrounded the
moment someone checks.

```diff
-- **A token budget.** Rejected: L1 (a tokenizer per model family), and an
-  approximation the caller cannot audit.
+- **A token budget.** Rejected: an approximation the caller cannot audit —
+  decision 10's ground, and since 2026-09-06 the **only** one. ⚠ The L1 leg
+  (*"a tokenizer per model family"*) fell with ADR-LAWS decision 9: a
+  tokenizer is now *legal* behind an extra. **It is still refused**, because
+  an approximate token count is wrong in a way the caller cannot see, and an
+  exact byte count is not.
```

```diff
-- **An HTTP client in `src/fux/refer/`.** Rejected: L1, L4 and the adapter cap,
-  and it duplicates a contract that already exists and already ships.
+- **An HTTP client in `src/fux/refer/`.** Rejected: L4 and the adapter cap,
+  and it duplicates a contract that already exists and already ships. ⚠ The
+  L1 leg fell 2026-09-06; **L4 alone is sufficient and always was.**
```

Decision 10's inline *"carrying a tokenizer per model family violates L1"* needs
the same treatment — strike the clause, keep the sentence after the `and`.

### 3c. Records needing **no** change

- **ADR-RERANK (0041)** — the cross-encoder refusal is *"cross-machine
  determinism, not cost"*. L3. Untouched. Its `laws: [L1, L3, L4]` stays
  accurate: the reranker is stdlib arithmetic on a core path.
- **ADR-EXTRACTED (0016)**, **ADR-ASK (0004)**, **ADR-RANKING (0012)**,
  **ADR-QUALITY (0044)**, **ADR-OUTPUT (0047)** — all cite L1 for *core* paths,
  which the amendment leaves stdlib. `laws:` keys unchanged.
- **`docs/adr/README.md` line 313** — `hand-rolled parser — L1, `$0` stdlib-only`.
  Still true of `frontmatter.py`. Optional tidy, not required.

---

## 4. ⚠ What this does not buy you — read before approving

You picked all four drivers. Two of them are **not served** by this change.

| your driver | served? | why |
|---|---|---|
| **Format / decode capability** | ✅ **yes, fully** | Pillow, pypdf, OCR all become legal behind extras. This is the driver the amendment actually pays for. |
| **Build velocity** | ✅ **partly** | Real for new codecs. Not for existing ones — the amended law bars rewriting a working hand-rolled codec onto a library, and that is where the sunk hand-rolling already is. |
| **Chunking / retrieval quality** | ❌ **no** | Blocked by **L3** (no model in the maintenance path) and ADR-RERANK's determinism refusal. Removing L1 entirely would not have unblocked it either. And per the research I ran: the model-driven chunking families **lose** to the deterministic structural chunker you already have. |
| **Positioning** | ⚠ **it changes it, downward** | You are trading *"there is no dependency tree"* for *"the dependency tree is short and free"*. That is a weaker claim to an enterprise buyer, and the default install is the only thing holding the original pitch up. |

**If the chunking row is the one that mattered, this is the wrong law and the
next conversation is L3 — a much larger one.** Say so and I will scope it
separately.

---

## 5. Files touched — the full checklist

| file | change | required by |
|---|---|---|
| `CLAUDE.md` | §Non-negotiable constraints, L1 block | the ruling |
| `docs/adr/0001_laws.md` | §1 table row + decision 9 + veto check 2 & 2b | ADR-LAWS d4 |
| `docs/adr/0042_decode.md` | alternatives, reopen-trigger 2, line ~222 | Law zero |
| `docs/adr/0030_refer-plane.md` | decision 10 + two alternatives | Law zero |
| `pyproject.toml` | comment on `dependencies = []` | fact correction |
| `README.md` line 119 | the Laws line | fact correction |
| `work/WORKLOG.md` | one entry, newest on top | three-file discipline |
| `work/INTERVIEW.md` | standing-constraints section | three-file discipline |
| `work/DOC-REGISTRY.md` | bump every row above | required |
| `work/OPEN-WORK.md` | new agent-lane row for the L1 test | same-change rule |
| `tests/test_l1_dependencies.py` | **new** — see §2c | two-strikes rule |

### `pyproject.toml`

```diff
-# stdlib only — $0, deterministic, dependency-free runtime (see CLAUDE.md).
+# The default install is dependency-free and stays that way — L1 (see CLAUDE.md).
+# Third-party FOSS is legal only under [project.optional-dependencies], never here.
 dependencies = []
```

### `README.md` line 119

```diff
-- **Laws:** $0 default · stdlib-only · byte-deterministic · offline by
-  default · one ADR per feature, every rule referenced.
+- **Laws:** $0 and free-software-only · a dependency-free default install ·
+  byte-deterministic · offline by default · one ADR per feature, every rule
+  referenced.
```

⚠ **The README's opening pitch is not audited here.** Grep it for any *stronger*
zero-dependency claim before the commit; I checked the Laws line and the two
fetcher mentions (both accurate — `http.py` and `cdp.py` really are pure
stdlib), but not the marketing prose end to end.

### The new test — the reason to write it now

The old L1 was **unenforceable prose**. Nothing in `tests/` checked it; I looked.
The amended L1 has a mechanically checkable clause (*"the default install is
dependency-free"*), and your own two-strikes rule says a lesson recorded twice
becomes a gate in the change that records it. **This is the change.** Roughly:

```python
def test_default_install_has_no_runtime_dependencies():
    """L1: `pip install fux-engine` brings nothing with it."""
    assert tomllib.loads(PYPROJECT.read_text())["project"]["dependencies"] == []

def test_every_extra_is_free_software():
    """L1: no paid dependency, ever. Each extra is named in a record."""
    ...
```

The second one cannot be fully automated — licence checking needs a real
allowlist. **Write the first, ship it green, and say plainly in the docstring
that the paid-dependency clause rests on review.** Half a gate that says so
beats a whole gate that lies.

---

## 6. Commit

One commit. Message names the law change explicitly, per the
documentation-discipline rule that a `CLAUDE.md` edit is *said out loud*:

```
laws: amend L1 — $0 becomes FOSS-only; stdlib core with opt-in extras

Arpit's ruling, 2026-09-06. The default install stays dependency-free and
every core path stays stdlib; third-party FOSS becomes legal behind declared
optional extras, and numpy/pandas/scipy become legal in measurement harnesses.

Supersedes ADR-DECODE's "amending L1" alternative and rewrites its reopen
trigger 2. Strips the L1 leg from two ADR-REFER rejections, both of which
survive on their remaining grounds. Adds the first test L1 has ever had.

ADR-LAWS decision 9 carries what the amendment traded away: the trivially
auditable supply chain narrows to a short auditable one, and the default
install is now the only thing carrying the original promise.

CLAUDE.md edited — L1's normative text, per §Documentation discipline.
```
