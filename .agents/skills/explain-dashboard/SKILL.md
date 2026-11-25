---
name: explain-dashboard
description: Explain a number, term, tile, filter or surprising result on the GIA stop-out dashboard in plain language, and name the known issues that affect it. Use when someone asks what a dashboard figure means, why a term (such as Fall) looks missing, why counts changed after an upload, why two near-completer numbers differ, or whether a number is safe to share.
---

# explain-dashboard

Explain the stop-out dashboard to a subject-matter expert (advisor, dean, institutional researcher)
who knows students and programs but not software.

## Sources, in this order

1. `KNOWN_ISSUES.md`: bugs (B), caveats (C), things not yet tested (N), out-of-date documents (D).
2. `PLAYBOOK.md`: the definitions ("Words that mean one thing here"), the table "Where each number
   comes from", and the plays.
3. `RUNBOOK_UPLOADS.md`: for questions about uploading.
4. Only if those don't answer it: the app code in
   `../gia-datathon/playground/server_application/app/institution_dashboard/data.py`. Cite the
   function, and say that the answer came from the code.

Read the relevant sections each time. The documents change, so don't answer from memory.

## How to answer

1. **Short answer first,** in one or two plain sentences. No code names, no jargon. Say "the
   student file", not `students.csv`, unless the reader works with the files.
2. **Why,** in a few sentences.
3. **Which known issues apply,** by ID and title, with a link, for example
   `[C9 Term labels use the calendar year, not the academic year](KNOWN_ISSUES.md#c9-term-labels-use-the-calendar-year-not-the-academic-year)`. Links
   are relative to the repo root.
4. **What to do next,** if anything.

## Common questions and where the answer is

| Question | Look at |
| --- | --- |
| "Fall is missing" / "the years look off" | C9 (labels use the calendar year; before 2026-11-11 Fall showed as "Winter"), C5 (current term in progress), Playbook Play 8 "First, check whether the term is really missing" |
| "Stop-outs within N credits shows enrolled students" | B5, C10 |
| "Two near-completer numbers don't match" | C10, Playbook "Where each number comes from" |
| "Stop-outs jumped / fewer students after an upload" | C4, C1, C2 |
| "The list only shows 40 students" | C11 |
| "Course attempts or 'next offered' look wrong after an upload" | B1 |
| "High-DFW flags didn't change after an upload" | B4 |
| "Error: unknown filter" / "Something went wrong" | B2, B3 |
| "Can I share this number?" | C13 (small groups), C15 (hosted site is public) |
| "Can I upload on the hosted site?" | N1, C15, RUNBOOK_UPLOADS.md |

## Rules

- Never make up a number. If the person needs current figures, suggest the `data-health-check`
  skill, or reading them off the dashboard.
- Never show or ask for student IDs or names.
- Say the data is synthetic when it is the bundled sample data.
- If the documents don't cover the question, and the code doesn't settle it, say so plainly. Don't
  guess.
