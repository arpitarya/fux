# ANALYSIS — graph-acceptance, 2026-08-22

## The methodology deviation, stated plainly

W-57's own definition of done says the goldens are "written by a human,
**and no agent should do it**" — because a golden derived from the engine's
own output tests nothing, and TREC's discipline (independent assessors,
never the system under test) is the reason that rule exists.

**This run's goldens were written by the agent, at Arpit's direct
instruction, after the fux-playground redesign made "wait for a human to
write ~50 goldens" a plan with no corpus to write them against.** That is a
real deviation from the written rule, and it is recorded here rather than
left for a future reader to assume the rule was followed.

**Why it is a smaller deviation than it could have been:** the goldens are
not derived from what `fux` returned. They are derived from what the
**generator planted** — a fact fixed in code (`make_graph_corpus.py`,
`planted.json`) before any `fux` command ran against the corpus. The
independence TREC's rule protects is independence from the *system under
test's judgment of relevance* — not independence from any agent. Here, the
"assessor" (this agent) decided the ground truth by constructing it, the
same way the original playground and acme corpora were built by whoever
wrote their generators. The construction and the check are genuinely
different steps: `fux explain`/`fux path` were run once, before the goldens
file was finalized, **only to confirm the corpus's own markdown links
resolved into edges** — a bug was found and fixed this way (relative links
one directory too deep) — never to ask "what does fux think the answer is."

**What would make this untrustworthy, and is not what happened:** if the
"expected" node in a `graph` golden had been chosen by running `fux graph`
first and copying whatever it returned. That was not done — `expect_node` in
every planted golden is the document the generator explicitly wrote a
`supersedes`/`predecessor`/`superseded by` sentence about, decided before the
corpus existed as files on disk.

**The honest residual risk:** one person (this agent) authored both the
corpus and the goldens, in the same sitting, with no second reviewer. That is
weaker than an independent human assessor reading finished documents cold.
Arpit reviewing `evidence/planted.json` against the actual document bodies is
the check this analysis cannot perform on itself.

## Why 24 goldens, not ~50

fux-playground's contract calls for ~50 queries because its 10-document
corpus is *entirely* hand-planted hazards — every query is load-bearing.
This corpus's 66 documents are mostly **generic background** (12 ADRs, 5
runbooks, 8 guides, and so on) generated to give the graph lane real noise to
work against, with 7 explicitly planted pairs. 24 goldens is 3 checks
(`graph`/`path`/`explain`) per planted document pair, plus a small negative
and general set — proportionate to what was actually planted, not padded to
match a number from a different corpus's contract.

**What this does not cover, stated rather than left implicit:** goldens
against the 59 generic (non-planted) documents. A regression in ranking over
those documents would not be caught by this golden set. `tests_e2e/eval/relational`
(the small 5-doc fixture, 11/11) and fux-playground, if regraded, are the
other nets; this run does not replace either.

## Reproduce

```bash
cd ~/my_programs/fux-lab/graph-acceptance
./setup.sh              # generate -> fux setup -> ingest -> build
python3 check_graph.py  # PASS / FAIL and per-golden detail
```

Determinism of the corpus itself: run `shared/generate/make_graph_corpus.py`
twice into separate directories and `diff -rq` them.

## Recommendation

- **ADR-GRAPH veto condition 3**: update to record this run as evidence the
  phenomena improved, on a corpus distinct from the playground's own targets.
  Do not mark the condition permanently closed — a future playground regrade
  is still the more direct test of the original target.
- **Veto condition 1 (two machines)** stays open. Nothing in this run
  resolves it; a second machine is needed, not a bigger corpus.
- **W-52**: ~~this corpus is available as its required "second corpus"~~ —
  **struck 2026-08-22, wrong.** `graph-acceptance` declares one source dir
  (`docs`), no `archived=true`, and **0 of 66 records carry `archived`**. W-52
  asks what `df` over live-plus-archived does to live scoring; a corpus with no
  archived half cannot measure it. Two separate things were conflated here — a
  *second corpus* and a *corpus with an archived population* — and only the
  first was checked. W-44's instrument has since been built and **is** reusable
  for W-52's query set; the corpus half is not, and W-52's trigger stays unmet.
  **Also corrected in the report's opening section**, which made the same claim.
  Both struck rather than deleted, so the error stays visible.
