# VERDICT — W-298 step 1

**Ruling:** **PASS.** 19 of 20 intents place the expected rule in the top 5 of `fux ask`; the pre-set bar is 16 of 20.

**The frozen pre-registration this is ruled against** (verbatim from `work/open/W-298-packages-ship-their-index.md`, filed 2026-10-25, before any run):

> | 1 | Spike with today's fux: point `sources.yaml` at `node_modules/@codelaw/rules-js/rules`, write 20 plain-words intents, count how often the right rule is in the top 5. Bar set now: **16 of 20** | evidence that free-text search over rules is worth building for |

and its definition of done:

> Step 1's run is filed under `work/regression/` with its 20 intents, ranks and the pre-set bar (≥ 16 of 20 in the top 5); below the bar, this item closes as *parked* with the evidence.

**What was fixed before the first number:** the bar (in the item); the 20 intents and expected rules (`evidence/intents.tsv`, sha256 `cfe0c2f2be8698efa6684f6c4067c39059807b669f47032d508018f11bb68d29`, 2026-10-25 11:59:53 UTC). Nothing was edited after.

**What the verdict unblocks:** W-299 and W-302 (🟡 on this step → 🟢). W-300 and W-301 stay 🟡 on W-299.

**What it does not do:** rule on any ranking change (L13 is not engaged — nothing shipped); compare against any other run; speak for the 438-rule pack the item names, which is not the published 0.1.0.

`classification: informed` — see the report's §Authorship.
