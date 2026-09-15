# `tools/golden-difficulty/` — what makes a golden question hard, in numbers

**One file: [`difficulty.py`](difficulty.py).** It turns `difficulty` from a
label somebody felt into **a count of the independent discriminations a question
forces**, derived from the key and the corpus and re-derivable by anyone.

- **Owner:** [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 13.
- **Schema and bands:** [`work/golden/README.md`](../../work/golden/README.md)
  §*Difficulty* — stated once there, not here.
- **Item:** [W-190](../../work/open/W-190-question-difficulty.md).

## The three rules it exists to enforce

1. 🔴 **Difficulty is never derived from fux's own results.** *Hard = fux got it
   wrong* makes "fux is weaker on hard questions" true by construction. Nothing
   here reads a prediction, a score or an index.
2. 🔴 **Difficulty never ships in a released `questions/*.jsonl`.** A runner that
   can see a question is unanswerable abstains by arithmetic — the same reason
   `type` is withheld ([`work/golden/questions/README.md`](../../work/golden/questions/README.md)).
3. 🔴 **It refuses a key inside this repository, and that refusal is the point.**
   No answer key lives under this tree
   ([SR-LAW-11](../../records/0012_LAW-11-sealed-answer-key.md)); *"just point it
   at the repo copy"* is how a tool becomes the thing a law forbids, so it fails
   closed instead of trusting the caller.

## Running it

```bash
python3 tools/golden-difficulty/difficulty.py --selftest      # synthetic fixtures, no key

python3 tools/golden-difficulty/difficulty.py \
    --key ~/keys/golden-set-1.jsonl \
    --corpus ~/my_programs/fux-lab/corpora/golden/rung-01000 \
    --rung rung-01000 --out difficulty-rung-01000.jsonl
```

**Who runs it: Arpit or Codex**, because only they hold a key. **No Claude
session runs it with `--key`** — `--selftest` is the whole of what Claude can
exercise, and that is why the fixtures are synthetic and invented in the file
rather than drawn from the seed corpus.

## Two numbers, not one

- **`difficulty_static`** — frozen when the key is written, comparable across
  every rung: the flag list and the count `d`.
- **`distractors_at_rung`** — recomputed per rung: documents outside `relevant`
  carrying the question's top-IDF terms. **This is the honest one.** A lookup
  that is trivial against 20 documents is genuinely hard against 10 000, and the
  ladder exists to show that curve rather than assert it.

## What it cannot do

- **It cannot tell a well-written question from a badly-written one.** A vague
  question with one relevant document scores `easy` and is still a bad question.
  Difficulty is not quality; nothing here grades the key.
- **It measures the corpus as much as the question**, on purpose — which means a
  `distractors_at_rung` computed against a different ladder is not comparable,
  and the rung label is written into every row so nobody has to remember that.
- **A flag is a claim about structure, not about semantics.** `no_lexical_overlap`
  says the evidence shares no high-IDF term with the question; whether a reader
  would call that a paraphrase is a judgement the flag deliberately does not make.
