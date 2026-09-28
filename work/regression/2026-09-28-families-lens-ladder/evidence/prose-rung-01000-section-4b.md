## 4b · Families — documents grouped by shape

- 32 family(ies) of two or more, covering 911 of 1000 document(s) (**91.1 %**), at a heading-and-front-matter Jaccard >= 0.60 against every member.
- 16 misfit(s) — a member missing a heading >= 80.0 % of its family carries — **1.8 %** of family members (floor 20.0 %, *provisional*).
- 55 singleton(s); 34 document(s) with no headings, which have no shape to compare.

Levers: a misfit — `fux enrich`, `fux correct`, or fix the source; a family's shared headings — `[index]` stopwords, or an analyzer amendment — an index change, with its own record; a family split across folders — `.fuxignore`, `archived=`, or `supersedes` on the one that is current

| members | family | folders | front-matter keys | length |
|---|---|---|---|---|
| 138 | Day 1 to 3 · Day 7 | ext/adjacent/ | department, effective_date, owner, status, title | <200 |
| 136 | components · deductions · notes | ext/adjacent/ | — | <200 |
| 91 | What this edition said · Why it changed · Do not use this document to | ext/archive/ | effective_date, owner, status, title | <200 |
| 74 | Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records | ext/sibling/, seed/archive/ | department, doc_id, effective_date, owner, status, title | 200–999 |
| 63 | Base rates · Surcharges | ext/archive/, ext/sibling/, seed/ | department, effective_from, owner, status, title | <200, 200–999 |
| 60 | Context · Decision · Reasons · Consequences | ext/archive/, ext/sibling/ | effective_date, owner, status, title | <200, 200–999 |
| 59 | Summary · Timeline · What went wrong · Actions | ext/sibling/ | effective_date, owner, status, title | <200 |
| 45 | Who is told, and how fast · Wording · Who signs | ext/sibling/ | effective_date, owner, status, title | <200 |
| 32 | Course syllabus · Aims · Schedule · Assessment | ext/filler/ | — | <200 |
| 31 | Release notes · 7.3.0 — 2021-02-18 · Added · Fixed | ext/filler/ | — | <200 |
| 30 | Beekeeping association minutes · Minutes · Winter losses · Apiary | ext/filler/ | — | <200 |
| 30 | Chess club bulletin · Bulletin · League · Club championship | ext/filler/ | — | <200 |
| 30 | Library acquisition list · Acquisitions · Withdrawals · Requests | ext/filler/ | — | <200 |
| 13 | 1. Daily limits · 2. Rest · 3. Exceptions · 4. Mobile phones, alcohol and seat belts | ext/sibling/ | doc_id, effective_date, owner, status, supersedes, title | <200 |
| 13 | Who is told, and how fast · Wording · Who signs | ext/sibling/ | effective_date, owner, status, supersedes, title | <200 |
| 9 | Vantorix Wiki - Dock scheduling rules · Dock scheduling rules · Customer class grace table · Late arrivals | ext/sibling/ | — | <200 |
| 8 | Cindermoor Wiki - Dock scheduling rules · Dock scheduling rules · Raipur DC · Customer class grace table | ext/sibling/ | — | <200 |
| 7 | Halberd & Frost Wiki - Dock scheduling rules · Dock scheduling rules · Customer class grace table · Late arrivals | ext/sibling/ | — | <200 |
| 6 | Zephyrine Wiki - Dock scheduling rules · Dock scheduling rules · Customer class grace table · Late arrivals | ext/sibling/ | — | <200 |
| 4 | Cold room mapping study TMS-41 · 1. Scope · 2. Probe grid · 3. Results | seed/ | department, doc_id, effective_date, facility, owner, room, status, title | 200–999 |

**Misfits, worst first:**

- `file:seed/archive/a01-sop-temperature-excursion-rev2.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP, 4. Immediate containment
- `file:ext/filler/a15-release-notes-tilecutter.md` — in *Release notes · 7.3.0 — 2021-02-18 · Added · Fixed*, missing Release notes
- `file:ext/sibling/00046-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00116-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00186-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00256-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00326-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00396-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00466-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00536-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00606-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00673-dockwiki.html` — in *Cindermoor Wiki - Dock scheduling rules · Dock scheduling rules · Raipur DC · Customer class grace table*, missing Raipur DC
- `file:ext/sibling/00676-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00746-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00816-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP
- `file:ext/sibling/00886-quarantine.md` — in *Temperature Excursion Response SOP · 1. Purpose · 2. Products and limits · 3. Approved records*, missing Temperature Excursion Response SOP

