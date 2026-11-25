# Stop-out and near-completer playbook

How to use the GIA datathon dashboard (in the `gia-datathon` repo) to find students who left close to
finishing, decide who reaches out, and check the numbers yourself.

> **The data can change at any time.** Each college's CSVs can be replaced through the dashboard's
> Upload page, and a second year of data changes how stop-outs are counted. This playbook has no fixed
> numbers on purpose. To see the current ones, run [`dashboard_counts.py`](scripts/dashboard_counts.py),
> or compare it with the app using [`verify_against_api.py`](scripts/verify_against_api.py).
>
> **Until a college uploads its own files, the data is synthetic.** Nothing built on it is a finding
> about real students or either college. Say so whenever you share a number.

Paths are relative to the `gia-datathon` repo unless they start with `scripts/` or `sql/` (this repo).
The scripts expect the two repos side by side. If they aren't, set `GIA_REPO=/path/to/gia-datathon`.
Function names refer to `playground/server_application/app/institution_dashboard/data.py` unless
another file is named.

## Pick your play

| You are | You want to | Play |
| --- | --- | --- |
| Anyone | See the dashboard running | [1](#play-1-run-the-dashboard) |
| Executive | Know how many students stopped out, and how many were close | [2](#play-2-read-the-executive-view) |
| Advisor or student services | See who is close to finishing | [3](#play-3-see-who-is-close-to-finishing) |
| Academic affairs | Look at one major | [4](#play-4-look-at-one-major) |
| IR analyst | Load your own year-by-year files | [5](#play-5-load-your-own-data) |
| IR analyst | Check the dashboard's numbers without the app | [6](#play-6-check-the-numbers-with-sql) |
| Analyst or developer | Report near completers as a success measure | [7](#play-7-near-completers-as-a-measure) |
| IR analyst or developer | Add or fix data, for example a missing Fall term | [8](#play-8-add-or-fix-data-for-example-a-missing-fall-term) |

Before quoting any number, read [Known issues](KNOWN_ISSUES.md): the bugs and caveats, in plain language. To upload data through the browser, follow the [upload runbook](RUNBOOK_UPLOADS.md). For a list of every skill, script and command, see the [Toolbox](TOOLBOX.md).

## Words that mean one thing here

| Term | Means | Code |
| --- | --- | --- |
| **In scope** | Every student except `student_type` = `Non-credit (MASP included)` | `OUT_OF_SCOPE_TYPES` |
| **Left out** | In scope, with `excluded_from_outreach` = true (CVC students). Left out unless that student type is picked in the filter | `build_dashboard` |
| **Measured** | In scope and not left out. Most counts use these students | `measured_students` |
| **Current term** | The latest `Last Enrolled Term` among in-scope students. It moves when newer data is uploaded | `_current_term` |
| **Credits left** | `Units Remaining` (CMC) or `Credits Remaining` (College 2), read from `students.csv` as given | `_students` |
| **Near completer** | More than 0 and at most *threshold* credits left. With no threshold (the default), the dashboard's "near completers" are every stop-out | `_is_near`, `build_dashboard` |
| **Threshold** (credit filter) | `stop_outs` ("All stop-outs", the default: no credit band) or 0, 3, 6, 9, 12, 15, 24. Any other value gets a 422 | `parse_credits`, `THRESHOLDS` |
| **Threshold 0** | Means "haven't started": no credits applied to the program yet. It does **not** mean 0 credits left | `_is_near` |
| **Left with credits** | Still owes credits, and left. In single-year mode "left" means `Currently Enrolled` is not `Yes`. In multi-year mode it means missing from the newest `pdp_year` | `_left_with_credits` |
| **Stop-out** | Left with credits, in a term **before** the current term | `_is_stop_out` |
| **Not enrolled this term** (pending) | Left with credits, in the current term. Not counted as a stop-out until the term is over | `_is_pending` |
| **Single-year / multi-year mode** | Multi-year only when an upload is in use **and** its `students.csv` has 2 or more `pdp_year` values. Otherwise single-year, including the synthetic files, which have several `pdp_year` values but are a snapshot | `is_multi_year` |

## Where each number comes from

"Near completers" means different people in different places. Say which one you mean. (Known issue [C10](KNOWN_ISSUES.md#c10-near-completers-means-different-groups-in-different-places))

| Number | Who it counts | Code |
| --- | --- | --- |
| Summary: Students | In scope (left-out students included) | `build_dashboard` |
| Summary: Near completers | Default: every measured stop-out. With a threshold: measured students within it, **enrolled or not** | `near` in `build_dashboard` |
| Summary: Stop-outs, and the "Stopped out" tile | Measured stop-outs in the chosen term range | `_is_stop_out`, `_stop_out_tiles` |
| Rate and second tile ("Still owing credits" by default, else "Within N credits of finishing") | Stop-outs in the band: **among stop-outs** only | `rates`, `_stop_out_tiles` |
| Student table | The summary's near completers, narrowed by program, hold, parent and last term enrolled | `listed` in `build_dashboard` |
| Program counts, cohort trend | The summary's near completers, by program or cohort | `_program_counts`, `trend` |
| Pathway charts | Stop-outs in the term range, narrowed by their own credit setting (`pathway_credits`), separate from the page's | `charted` in `build_dashboard` |
| Stop-outs by term | Stop-outs, by the term they left | `stop_outs` in `build_dashboard` |
| `near_completers` measure (`measures/`) | Near completers among all students the measure covers, enrolled or not. Students who earned a credential and CVC students are outside it. **Reads the synthetic files only** | `measures/load_synthetic.py` |

## Play 1: Run the dashboard

You need the playground installed once: `mise run api:install && mise run web:install` from
`playground/` (see the main README's Quick start). Then, in two terminals:

```bash
cd playground/server_application
APP_ENV=development .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd playground/client_application
node node_modules/next/dist/bin/next dev --port 3000
```

Open http://localhost:3000. It opens on the executive view, and the API docs are at
http://localhost:8000/docs. Every view (executive, student services, academic, financial) shows
sections of the same `/api/v1/dashboard` response for the same filters.

## Play 2: Read the executive view

The three tiles count **stop-outs** under the filters you picked:

- **Stopped out:** stop-outs who left inside the term range.
- **Second tile:** follows the credit filter. "Still owing credits" with the default "All
  stop-outs" (the same number as the first tile), or "Within N credits of finishing" with a number.
- **Term with the most stop-outs:** when outreach demand peaks.

Before you quote a tile:

- Check the tile note for the term in progress. Students who left in it are not counted yet.
- Check whether an upload is in use and which mode applies. The Upload page shows the rule as
  `stop_out_basis`, and `dashboard_counts.py` prints both.
- The term range filters **stop-outs only**. It doesn't change near-completer counts or the student
  table.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C5](KNOWN_ISSUES.md#c5-newer-terms-move-the-current-term), [C9](KNOWN_ISSUES.md#c9-term-labels-use-the-calendar-year-not-the-academic-year), [C12](KNOWN_ISSUES.md#c12-the-term-range-only-affects-stop-out-counts).

## Play 3: See who is close to finishing

What the student table lists depends on the credit filter. With the default "All stop-outs" it lists
stop-outs. With a number of credits it lists near completers, **enrolled or not**, even though the
choice reads "Stop-outs within N credits" ([B5](KNOWN_ISSUES.md#b5-a-stop-outs-within-n-credits-choice-also-lists-enrolled-students)). It is sorted by
credits left and narrowed by the program, hold, parent and "Last term enrolled" filters.

```bash
curl -s 'localhost:8000/api/v1/dashboard?institution=college_two&credit_threshold=9&hold=yes&parent=yes'
```

| Parameter | Values |
| --- | --- |
| `institution` | `cmc`, `college_two` |
| `credit_threshold` | `stop_outs` (default) or 0, 3, 6, 9, 12, 15, 24 |
| `pathway_credits` | The pathway charts' own credit setting: `stop_outs` (default) or a number as above |
| `student_term` | `all`, or one term: narrows the student list by last term enrolled |
| `student_type` | `all`, or one or more types from the data joined with `\|`. Unknown types return 422 |
| `campus_location`, `program` | `all`, or a value from the data. Unknown values return 422 |
| `hold`, `parent` | `any`, `yes`, `no` |
| `term_from`, `term_to` | `all`, or a term someone stopped out in. Stop-outs only |

- **The list stops at 40 students.** `students_matched` gives the full count. There is no full
  export.
- The rows carry student IDs. Keep them inside the college's systems, and don't paste them into chat
  tools.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C10](KNOWN_ISSUES.md#c10-near-completers-means-different-groups-in-different-places), [C11](KNOWN_ISSUES.md#c11-the-student-list-shows-at-most-40-students), [C12](KNOWN_ISSUES.md#c12-the-term-range-only-affects-stop-out-counts), [C13](KNOWN_ISSUES.md#c13-small-groups-are-not-always-hidden).

## Play 4: Look at one major

```bash
curl -s 'localhost:8000/api/v1/dashboard/major?institution=cmc&major=BIOLOGY&credit_threshold=9'
```

It returns:
- The major's student count.
- Its near completers and stop-outs.
- Shares of parenting, working, on hold and not enrolled. These are hidden under 10 students.
- The courses its near completers still owe (or, if it has none, the courses everyone in the major
  still owes), with when each course runs.

The major must be listed in `pathway_map.csv`. See the gotchas.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C7](KNOWN_ISSUES.md#c7-new-majors-need-to-be-added-to-the-major-list-separately).

## Play 5: Load your own data

> Not a technical user? Follow the [upload runbook](RUNBOOK_UPLOADS.md) instead: the same steps in the browser, with a checklist.

The Upload page (`/dashboard/upload`) saves one college's four CSVs. To see the columns it requires
and the years it has saved:

```bash
curl -s 'localhost:8000/api/v1/uploads/requirements?institution=cmc'
```

Then send all four at once:

```bash
curl -s -X POST 'localhost:8000/api/v1/uploads?institution=cmc' \
  -F students=@students.csv \
  -F profile=@student_institutional_profile.csv \
  -F course_schedule=@course_schedule.csv \
  -F course_detail=@course_detail.csv
```

| Action | What happens |
| --- | --- |
| Upload a year | `students.csv` and `course_detail.csv`: the uploaded years replace the same years, and other years stay. The profile and schedule files are replaced whole |
| Upload a second year | The college switches to multi-year mode, and stop-outs are counted by who is missing from the newest year |
| `DELETE /api/v1/uploads?institution=cmc&year=2024-25` | Drops one saved year |
| `DELETE /api/v1/uploads?institution=cmc` | Deletes the upload. The college goes back to the synthetic files |

After any upload, run [Play 6](#play-6-check-the-numbers-with-sql) to confirm what the dashboard now
reads.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C1](KNOWN_ISSUES.md#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it), [C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted), [N1](KNOWN_ISSUES.md#n1-uploading-on-the-hosted-dashboard).

## Play 6: Check the numbers with SQL

[`scripts/dashboard_counts.py`](scripts/dashboard_counts.py) works out the executive numbers from the
CSVs. It needs only Python 3.10 or newer: no packages to install. (On Windows, type `py` instead of
`python3`.) The SQL is in [`sql/dashboard_counts.sql`](sql/dashboard_counts.sql), with
each step naming the app function it copies, so it can be ported to a college's warehouse.

```bash
python3 scripts/dashboard_counts.py college_two                   # the default: all stop-outs
python3 scripts/dashboard_counts.py cmc 9
python3 scripts/dashboard_counts.py cmc 9 --data-dir /abs/path    # the app's DASHBOARD_DATA_DIR, if set
python3 scripts/dashboard_counts.py cmc 9 --upload-dir /abs/up    # the app's DASHBOARD_UPLOAD_DIR, if set
```

- **Which folder it reads:** the same folder the app reads. That is the saved upload in
  `<upload folder>/<college>/` if there is one, or the synthetic files otherwise. The upload
  folder is `DASHBOARD_UPLOAD_DIR` (or `--upload-dir`) if set, else `<data root>/uploads`. Production
  sets it to `/tmp/dashboard-uploads`, so pass `--upload-dir` when checking a production-like setup. The script
  prints the folder, whether an upload is in use, the `pdp_year` values, and the mode.
- **What it prints:** the summary counts, both stop-out rates, stop-outs by term, and near completers
  by program. These all use the default filters ("all" and "any").
- **What it refuses:** a threshold the app refuses, a missing required column, a blank or
  non-numeric credits value, and a student with no profile row. The app fails on those last two, so
  the script refuses rather than print a number.

To confirm it agrees with a running app:

```bash
python3 scripts/verify_against_api.py cmc 9                                  # local API on :8000
python3 scripts/verify_against_api.py cmc 9 --api http://localhost:8001/api/v1 --data-dir /abs/path
```

It compares every number and exits 1 on any difference.

From Python (a notebook, for example), both work as functions:

```python
import sys
sys.path.append("/path/to/gia-datathon-cookbooks/scripts")
from dashboard_counts import dashboard_counts
from verify_against_api import compare

result = dashboard_counts("cmc", 9)              # same options: data_dir=..., upload_dir=...
result.value("summary", "stop_outs")             # one number
import pandas as pd; pd.DataFrame(result.rows)   # every number, as a table
compare("cmc", 9)                                # [] when the running API agrees
```

A data problem raises `dashboard_counts.DataProblem`, with the same message the command prints. The
tests are in `tests/`: `python3 -m unittest discover -s tests`.

**Checked:** it matched the API on every threshold for both colleges on the synthetic files. It also
matched on a multi-year CMC upload: two `pdp_year` values, header reordered, byte-order mark (BOM),
Windows line endings.

## Play 7: Near completers as a measure

From the repo root, with `.venv` active:

```python
from measures.load_synthetic import load
from measures.models import Cohort, GroupBy, GroupDimension, Measure
from measures.run_measures import run_measure

college_two = load("college_two")
rows = run_measure(Measure.NEAR_COMPLETERS, [Cohort.of("2023-24")],
                   [GroupBy.of(GroupDimension.MAJOR)], database=college_two, threshold=9)
for r in rows:
    print(r.group, r.status, r.numerator, r.denominator, r.metric_rate)
```

Groups under 10 students come back `suppressed`, with no numbers. The measure reads the **synthetic
files only**, so after an upload it no longer describes what the dashboard shows.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C14](KNOWN_ISSUES.md#c14-the-success-measures-and-other-tools-ignore-uploads), [D1](KNOWN_ISSUES.md#d1-old-near-completer-figures-in-the-measures-readme).

## Play 8: Add or fix data (for example a missing Fall term)

### First, check whether the term is really missing

Three things make a Fall term look missing when it isn't:

| What you see | Why | Code |
| --- | --- | --- |
| Fall and Spring of one academic year look like different years | Terms are labeled by calendar year: Fall 2024 shows as "24 Fall", Spring 2025 as "25 Spring". Both are `2024-25`. (Before 2026-11-11, Fall showed as "24-25 Winter") | `term_label` |
| The newest Fall is missing from stop-outs by term | It is the current term, still in progress. Students who left in it are counted as "not enrolled this term", not as stop-outs | `_current_term`, `_is_pending` |
| A Fall term is missing from the term filter | The filter lists only terms in which someone stopped out | `build_dashboard` |

`python3 scripts/dashboard_counts.py <college>` prints raw term names (`Fall 2024`), the current term, and
stop-outs by term, so you can see what the data holds without the labels.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C5](KNOWN_ISSUES.md#c5-newer-terms-move-the-current-term), [C9](KNOWN_ISSUES.md#c9-term-labels-use-the-calendar-year-not-the-academic-year).

### How terms are written

| Where | Column | Format |
| --- | --- | --- |
| `students.csv` | `Last Enrolled Term` | `Spring 2025`, `Summer 2025`, `Fall 2025`. Sorted by year, then Spring < Summer < Fall. Any other season (`Winter`) sorts like Spring, and any other shape sorts before everything (`term_key`) |
| `students.csv` | `pdp_year` | `2024-25`. **Fall starts the academic year:** Fall 2024 and Spring 2025 are both `2024-25`. Required on every row of an upload. The app takes it as given and does not derive it from the term |
| `students.csv` | `Currently Enrolled` | `Yes` or anything else. In single-year mode, this decides who has left |
| `course_detail.csv` | `Academic Year`, `Enrollment Term`, `Status` | Same term format. Rows with `Status` = `In Progress` set the term in progress for course timing |
| `course_schedule.csv` | `terms_offered`, `offering_pattern` | For example `fall; spring`. Used for "next offered" on courses still owed |

Credits left (`Units Remaining` / `Credits Remaining`, and `Credits Applied to Program`) are not
recalculated from new course rows. If you add courses, update those columns yourself.


> Also listed in [Known issues](KNOWN_ISSUES.md): [C6](KNOWN_ISSUES.md#c6-credits-remaining-are-used-exactly-as-uploaded), [C8](KNOWN_ISSUES.md#c8-term-names-must-be-written-one-way).

### Option A: through the Upload page

This works on any running copy of the app. To add Fall 2024, upload the academic year `2024-25`:

1. **Send the whole academic year,** not just Fall. An upload replaces every year it contains, so a
   file with only the Fall 2024 rows would drop the Spring 2025 rows of `2024-25`.
2. **The first upload replaces the synthetic data for that college; it is not added to it.** Saved
   years only combine with earlier uploads (`_merged` in `uploads.py`). To add one term to the
   synthetic data, upload all the years you want to keep.
3. **Send complete profile and schedule files.** They replace the saved ones whole. Every student in
   any saved year needs a profile row, or `/dashboard` returns 500.
4. **Known bug: `course_detail.csv` loses rows on upload.** The app keeps one row per student per
   `pdp_year` (`YEAR_KEYED` and `_merged` in `uploads.py`). Uploading the synthetic CMC file kept
   1,000 of 15,797 rows. Adding a `pdp_year` column kept 3,055. Student counts, near completers
   and stop-outs are not affected, and neither is the list of courses each student still owes.
   What is affected: attempt counts on those courses, and "in progress" / "next offered". Use
   Option B if you need those until the app is fixed. (Known issue [B1](KNOWN_ISSUES.md#b1-uploading-course-history-throws-most-of-it-away).)
   Separately, the "high DFW" course flags always describe the sample data (Known issue
   [B4](KNOWN_ISSUES.md#b4-course-drop-and-fail-rates-ignore-uploads).)
5. **Check the result:** run `python3 scripts/dashboard_counts.py <college>` against the same data root.
   Confirm the `pdp_year` list, the mode, and the current term.

What changes when you add a year:

- **The first upload, with only one year:** single-year mode. "Left" means not currently enrolled.
- **A second or later year:** multi-year mode. Stop-outs are students missing from the newest year.
- **A year newer than any saved one:** it becomes the year everyone is measured against, and its
  terms can move the current term.
- **An older year:** the newest year stays the same. Students who appear only in the older year are
  missing from the newest year, so any who still owe credits become stop-outs.
- **To undo:** `DELETE /api/v1/uploads?institution=<college>&year=2024-25` drops the year, and
  `DELETE /api/v1/uploads?institution=<college>` goes back to the synthetic files.


> Also listed in [Known issues](KNOWN_ISSUES.md): [B1](KNOWN_ISSUES.md#b1-uploading-course-history-throws-most-of-it-away), [B3](KNOWN_ISSUES.md#b3-a-student-with-no-profile-row-breaks-the-dashboard), [C1](KNOWN_ISSUES.md#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it), [C2](KNOWN_ISSUES.md#c2-uploading-a-year-replaces-that-whole-year), [C3](KNOWN_ISSUES.md#c3-the-profile-and-schedule-files-are-replaced-whole), [C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted), [N1](KNOWN_ISSUES.md#n1-uploading-on-the-hosted-dashboard).

### Option B: edit a copy of the CSVs (local API only)

Use this when the Upload page's limits get in the way, or to try a change before uploading it.

```bash
cp -R gia-pre-implementation/synthetic-datasets /abs/path/my-data   # never edit the repo's copy
# edit /abs/path/my-data/<college>/csv/*.csv: add or change rows, in the formats above
cd playground/server_application
DASHBOARD_DATA_DIR=/abs/path/my-data APP_ENV=development .venv/bin/python -m uvicorn app.main:app --port 8000
```

Then, from this repo:

```bash
python3 scripts/dashboard_counts.py cmc 9 --data-dir /abs/path/my-data
python3 scripts/verify_against_api.py cmc 9 --data-dir /abs/path/my-data
```

- Files in `<data root>/<college>/csv/` are always read in **single-year** mode. To use the
  multi-year rule, put all four files in `<data root>/uploads/<college>/` instead. The app reads
  them as they are, without the upload merge, so `course_detail.csv` keeps every row. This is how
  the multi-year check in Play 6 was run.
- Keep `pathway_map.csv` at the data root. The major view and the pathway charts read it.
- Don't edit `gia-pre-implementation/synthetic-datasets/` itself: the files are tracked in git and
  shared by every squad, and `rebuild_major_progress.py` rewrites their progress columns.

## Bugs and caveats

These are all in [Known issues](KNOWN_ISSUES.md), with what you'll notice, what is going on, and what
to do:

| Kind | Entries |
| --- | --- |
| Bugs | [B1](KNOWN_ISSUES.md#b1-uploading-course-history-throws-most-of-it-away), [B2](KNOWN_ISSUES.md#b2-a-blank-credits-value-gives-a-misleading-error), [B3](KNOWN_ISSUES.md#b3-a-student-with-no-profile-row-breaks-the-dashboard), [B4](KNOWN_ISSUES.md#b4-course-drop-and-fail-rates-ignore-uploads), [B5](KNOWN_ISSUES.md#b5-a-stop-outs-within-n-credits-choice-also-lists-enrolled-students) |
| Caveats when loading data | [C1](KNOWN_ISSUES.md#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it), [C2](KNOWN_ISSUES.md#c2-uploading-a-year-replaces-that-whole-year), [C3](KNOWN_ISSUES.md#c3-the-profile-and-schedule-files-are-replaced-whole), [C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted), [C5](KNOWN_ISSUES.md#c5-newer-terms-move-the-current-term), [C6](KNOWN_ISSUES.md#c6-credits-remaining-are-used-exactly-as-uploaded), [C7](KNOWN_ISSUES.md#c7-new-majors-need-to-be-added-to-the-major-list-separately), [C8](KNOWN_ISSUES.md#c8-term-names-must-be-written-one-way) |
| Caveats when reading the dashboard | [C9](KNOWN_ISSUES.md#c9-term-labels-use-the-calendar-year-not-the-academic-year), [C10](KNOWN_ISSUES.md#c10-near-completers-means-different-groups-in-different-places), [C11](KNOWN_ISSUES.md#c11-the-student-list-shows-at-most-40-students), [C12](KNOWN_ISSUES.md#c12-the-term-range-only-affects-stop-out-counts), [C13](KNOWN_ISSUES.md#c13-small-groups-are-not-always-hidden) |
| Caveats when comparing with other tools | [C14](KNOWN_ISSUES.md#c14-the-success-measures-and-other-tools-ignore-uploads) |
| Privacy | [C15](KNOWN_ISSUES.md#c15-the-hosted-dashboard-is-open-to-anyone-with-the-link) |
| Not checked | [N1](KNOWN_ISSUES.md#n1-uploading-on-the-hosted-dashboard) |
| Out-of-date documents | [D1](KNOWN_ISSUES.md#d1-old-near-completer-figures-in-the-measures-readme) |

## When something looks wrong

| You see | Why | Do |
| --- | --- | --- |
| `422 Unsupported credit threshold` | The threshold isn't 0, 3, 6, 9, 12, 15 or 24 | Pick one of those |
| `422 Unknown filter for this institution` | An unknown filter value, **or** a blank or non-numeric credits value in the data ([B2](KNOWN_ISSUES.md#b2-a-blank-credits-value-gives-a-misleading-error)) | Run `dashboard_counts.py`. It names data problems |
| `500` from `/dashboard` after an upload | A student with no profile row is a likely cause ([B3](KNOWN_ISSUES.md#b3-a-student-with-no-profile-row-breaks-the-dashboard)) | Run `dashboard_counts.py` |
| Stop-outs jump after an upload | The college switched to multi-year mode, or the newest year is partly loaded ([C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted)) | Check the mode and the `pdp_year` list `dashboard_counts.py` prints |
| `verify_against_api.py` shows differences | The script and the API read different folders, or the app's logic changed | Pass the API's data root with `--data-dir`. If it still differs, the SQL needs updating |
| The measure and the dashboard disagree | They count different students, and the measure ignores uploads ([C10](KNOWN_ISSUES.md#c10-near-completers-means-different-groups-in-different-places), [C14](KNOWN_ISSUES.md#c14-the-success-measures-and-other-tools-ignore-uploads)) | Say which one you mean |
