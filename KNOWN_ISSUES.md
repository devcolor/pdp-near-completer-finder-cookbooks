# Known issues: bugs and caveats

This page is for the people who use the stop-out dashboard's numbers: advisors, deans, and
institutional researchers. It assumes you know students and programs well. It does not assume you
know how the software is built.

It has four kinds of entries:

| Kind | Means | Entries |
| --- | --- | --- |
| **Bug** | The dashboard does something wrong. It needs fixing in the app. | [B1](#b1-uploading-course-history-throws-most-of-it-away) to [B5](#b5-a-stop-outs-within-n-credits-choice-also-lists-enrolled-students) |
| **Caveat** | The dashboard works as designed, but the result can surprise you or be misread. | [C1](#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it) to [C15](#c15-the-hosted-dashboard-is-open-to-anyone-with-the-link) |
| **Not checked** | Nobody has tested this yet. Don't rely on it. | [N1](#n1-uploading-on-the-hosted-dashboard) |
| **Out-of-date document** | A document elsewhere gives a figure that no longer matches. | [D1](#d1-old-near-completer-figures-in-the-measures-readme) |

Every entry says what you'll notice, what is going on, and what to do. **Also in** points to where the
[playbook](PLAYBOOK.md) mentions the same thing. The line **For developers** names the code, so the
team knows where to look. You can skip it.

The sample data that ships with the dashboard is made up. Nothing in it is a finding about real
students or either college.

---

## Bugs

### B1. Uploading course history throws most of it away

- **What you'll notice:** after an upload, the details on courses a student still owes look wrong:
  how many times the student attempted or failed each course, and whether it is "in progress" or
  when it is next offered. The list of courses each student still owes is right, and so are the
  student counts, near completers and stop-outs.
- **What's going on:** the course history file (`course_detail.csv`) has one row for every course
  every student took. When it is uploaded, the dashboard keeps only **one course per student per
  academic year** and quietly drops the rest. In a test with the Copper Mountain sample, 15,797
  course rows went in and 1,000 were kept. Adding a `pdp_year` column to the file only raised it to
  3,055.
- **What to do:** until it is fixed, don't rely on attempt counts or "next offered" after an upload.
  If you need them, ask a technical teammate to load the files directly instead of through the
  Upload page (playbook, Play 8, Option B). Loaded that way, every row is kept.
- **Also in:** [Playbook, Play 8, Option A](PLAYBOOK.md#option-a-through-the-upload-page), step 4.
- **For developers:** `_merged` and `YEAR_KEYED` in `playground/server_application/app/institution_dashboard/uploads.py`
  remove duplicates on (Student GUID, pdp_year), and that pair is not unique for course rows.

### B2. A blank credits value gives a misleading error

- **What you'll notice:** the dashboard shows an error that mentions an **unknown filter**, even
  though you didn't change any filter.
- **What's going on:** a student in the student file has a blank (or non-number) value for credits
  remaining or credits applied. The dashboard can't do arithmetic with it, and it reports this as a
  filter problem.
- **What to do:** run `python3 scripts/dashboard_counts.py <college>`, or ask a technical teammate to. It
  names the column and how many rows are affected. Fix those rows in the file and upload again.
- **Also in:** [Playbook, "When something looks wrong"](PLAYBOOK.md#when-something-looks-wrong).
- **For developers:** `float()` in `_students` (`data.py`) raises `ValueError`, which `routes.py`
  turns into the 422 "Unknown filter" response. Uploads don't check numeric columns.

### B3. A student with no profile row breaks the dashboard

- **What you'll notice:** the dashboard shows "Something went wrong on our side" for one college.
- **What's going on:** every student in the student file needs a matching row in the profile file
  (`student_institutional_profile.csv`, which holds holds, parenting and work). The profile file is
  replaced whole on every upload (see [C3](#c3-the-profile-and-schedule-files-are-replaced-whole)). If
  it leaves anyone out, including students from years uploaded earlier, the dashboard stops working.
- **What to do:** run `python3 scripts/dashboard_counts.py <college>`. It says how many students have no
  profile row. Upload a profile file that covers every student in every saved year.
- **Also in:** [Playbook, Play 8, Option A](PLAYBOOK.md#option-a-through-the-upload-page), step 3.
- **For developers:** `profiles[row["Student GUID"]]` in `_students` raises `KeyError`, which
  becomes a 500. Uploads don't check that the two files match.

### B4. Course drop and fail rates ignore uploads

- **What you'll notice:** after an upload, the courses flagged as often dropped or failed ("high
  DFW") are the same as before the upload.
- **What's going on:** the dashboard works out each course's drop and fail rates from the sample
  course history only, never from uploaded files. It also keeps those rates until the data service
  is restarted, so even replacing the sample files doesn't change them until a restart.
- **What to do:** treat the "high DFW" flags as describing the sample data, not your upload. A
  technical teammate who replaces the base files must restart the data service.
- **Also in:** [Deploy guide, "Restart after replacing the data files"](DEPLOY.md#restart-after-replacing-the-data-files).
- **For developers:** `_course_rates` in `data.py` reads `DATA_ROOT / institution / "csv" / "course_detail.csv"`
  (not `institution_folder()`), under `@lru_cache`.

### B5. A "Stop-outs within N credits" choice also lists enrolled students

- **What you'll notice:** you pick "Stop-outs within 9 credits", and the student list includes
  students who are currently enrolled. The near-completer count is also larger than the "Within 9
  credits of finishing" tile.
- **What's going on:** the credit filter's choices are labeled as stop-outs, but with a number
  chosen, the count and the list include everyone within that many credits, enrolled or not. Only
  the tiles and the rate count stop-outs alone. On the sample data at 9 credits, Copper Mountain
  showed 240 near completers against 105 stop-outs within 9 credits (checked 2026-11-11).
- **What to do:** to call only stop-outs, look at each student's enrollment in the list, or use
  the tile's count. Ask the team whether the label or the list should change.
- **Also in:** [C10](#c10-near-completers-means-different-groups-in-different-places).
- **For developers:** `CREDIT_OPTIONS` in `institution-view.tsx` labels every band "Stop-outs
  within N credits", but `build_dashboard` sets `near` to every measured student matching
  `_is_near` when a threshold is given, and `listed` is built from `near`.

---

## Caveats

### Loading or changing data

#### C1. The first upload replaces the sample data instead of adding to it

- **What you'll notice:** after uploading one year, the dashboard shows far fewer students than
  before.
- **What's going on:** the first upload for a college replaces all of its sample data. Only later
  uploads add to what was uploaded before. In a test, uploading one academic year of the Copper
  Mountain sample took the dashboard from 1,000 students to 94.
- **What to do:** to add a term to the sample data, upload every year you want to keep, not only the
  new one.
- **Also in:** [Playbook, Play 8, Option A](PLAYBOOK.md#option-a-through-the-upload-page), step 2.

#### C2. Uploading a year replaces that whole year

- **What you'll notice:** you upload a file with only the Fall rows, and that year's Spring students
  disappear.
- **What's going on:** data is stored by academic year, and **Fall starts the academic year**: Fall
  2024 and Spring 2025 are both `2024-25`. Uploading a year replaces everything saved for that year.
- **What to do:** always upload a complete academic year: Fall, Spring and Summer together.
- **Also in:** [Playbook, Play 8, Option A](PLAYBOOK.md#option-a-through-the-upload-page), step 1.

#### C3. The profile and schedule files are replaced whole

- **What you'll notice:** students or course sections from an earlier upload lose their details.
- **What's going on:** only the student and course history files are kept year by year. The profile
  and course schedule files have no year, so each upload replaces them entirely.
- **What to do:** every upload's profile and schedule files must cover all students and courses, not
  only the new year's. If the profile file leaves anyone out, see [B3](#b3-a-student-with-no-profile-row-breaks-the-dashboard).
- **Also in:** [Playbook, Play 8, Option A](PLAYBOOK.md#option-a-through-the-upload-page), step 3.

#### C4. Adding a second year changes how stop-outs are counted

- **What you'll notice:** the stop-out count jumps after an upload, sometimes by a lot. In a test, it
  went from 1 to 69 when a second year was added.
- **What's going on:** with one year of data, a stop-out is a student marked "not currently
  enrolled" who still owes credits. With two or more uploaded years, a stop-out is a student who
  **is missing from the newest year** and still owes credits. The sample data always uses the first
  rule. The Upload page shows which rule is in use.
- **What to do:** say which rule a number came from when you share it. If the newest year is only
  partly loaded, everyone missing from it looks like a stop-out, so load complete years.
- **Also in:** [Playbook, Play 5](PLAYBOOK.md#play-5-load-your-own-data) and
  [Play 8](PLAYBOOK.md#option-a-through-the-upload-page).

#### C5. Newer terms move "the current term"

- **What you'll notice:** students move between "stopped out" and "not enrolled this term" after an
  upload.
- **What's going on:** the dashboard treats the latest term in the data as still in progress.
  Students who left in that term aren't called stop-outs until it ends. New data with a later term
  moves that line.
- **What to do:** after an upload, check the current term the dashboard shows. `dashboard_counts.py`
  prints it too.
- **Also in:** [Playbook, Play 2](PLAYBOOK.md#play-2-read-the-executive-view) and
  [Play 8](PLAYBOOK.md#first-check-whether-the-term-is-really-missing).

#### C6. Credits remaining are used exactly as uploaded

- **What you'll notice:** you add course rows for a student, and their credits remaining don't change.
- **What's going on:** the dashboard reads credits remaining and credits applied straight from the
  student file. It never recalculates them from courses or the catalog.
- **What to do:** update the credits columns yourself whenever you add or change course records.
- **Also in:** [Playbook, Play 8, "How terms are written"](PLAYBOOK.md#how-terms-are-written).

#### C7. New majors need to be added to the major list separately

- **What you'll notice:** a major from your uploaded data can't be opened on its own (the major view
  gives an error), and it doesn't appear in the pathway charts.
- **What's going on:** the list of majors and their pathways (`pathway_map.csv`) isn't part of an
  upload. A major that isn't on that list can't be looked up.
- **What to do:** ask a technical teammate to add the major to `pathway_map.csv`.
- **Also in:** [Playbook, Play 4](PLAYBOOK.md#play-4-look-at-one-major).

#### C8. Term names must be written one way

- **What you'll notice:** terms show up in the wrong order, or not where you expect.
- **What's going on:** terms must read like `Fall 2024`, `Spring 2025` or `Summer 2025`. "Winter" is
  sorted as if it were Spring, and any other spelling is sorted before every real term. The
  academic-year column must read like `2024-25`.
- **What to do:** use only Spring, Summer and Fall, followed by a four-digit year.
- **Also in:** [Playbook, Play 8, "How terms are written"](PLAYBOOK.md#how-terms-are-written).

### Reading the dashboard

#### C9. Term labels use the calendar year, not the academic year

- **What you'll notice:** "24 Fall" and "25 Spring" look like different years, but they are in the
  same academic year.
- **What's going on:** the dashboard labels each term by its own calendar year: Fall 2024 shows as
  "24 Fall", Spring 2025 as "25 Spring". Academic years start in Fall, so both belong to `2024-25`
  (the `pdp_year` in the files). Until 2026-11-11 the dashboard showed Fall as "Winter" of the
  academic year ("24-25 Winter"), so notes or screenshots from before then may say Winter
.
- **What to do:** when matching a term to a `pdp_year`, a Fall term goes with the year it starts.
  `dashboard_counts.py` shows the full term names.
- **Also in:** [Playbook, Play 8](PLAYBOOK.md#first-check-whether-the-term-is-really-missing).

#### C10. "Near completers" means different groups in different places

- **What you'll notice:** two near-completer numbers that don't match.
- **What's going on:** it depends on the credit filter at the top of the page.
  - **"All stop-outs" (the default):** the "near completers" count and the student list are every
    stop-out still owing credits.
  - **A number of credits (for example "Stop-outs within 9 credits"):** the count and the student
    list switch to everyone within that many credits, **whether still enrolled or not** (see
    [B5](#b5-a-stop-outs-within-n-credits-choice-also-lists-enrolled-students)). The "Within 9 credits of finishing" tile still counts only students
    who **stopped out**.
  - The success measure in the `measures` folder counts a slightly different group again.
- **What to do:** always say which one you mean. The playbook's table spells out each one.
- **Also in:** [Playbook, "Where each number comes from"](PLAYBOOK.md#where-each-number-comes-from).

#### C11. The student list shows at most 40 students

- **What you'll notice:** the list stops at 40 even though the count above it is higher.
- **What's going on:** the list is capped at 40, and it is sorted by fewest credits remaining. With
  the default "All stop-outs" it lists stop-outs. With a number of credits it lists near completers,
  enrolled or not ([C10](#c10-near-completers-means-different-groups-in-different-places)). There is
  no full export.
- **What to do:** narrow the filters to get a list under 40, or ask for an export.
- **Also in:** [Playbook, Play 3](PLAYBOOK.md#play-3-see-who-is-close-to-finishing).

#### C12. The term range only affects stop-out counts

- **What you'll notice:** you change the term range and the near-completer numbers and the student
  list stay the same.
- **What's going on:** the term range filters students by the term they left, so it applies only to
  stop-outs. The student list has its own "Last term enrolled" filter for that.
- **Also in:** [Playbook, Play 2](PLAYBOOK.md#play-2-read-the-executive-view) and
  [Play 3](PLAYBOOK.md#play-3-see-who-is-close-to-finishing).

#### C13. Small groups are not always hidden

- **What you'll notice:** a program or a term shows a count of 2 or 3 students.
- **What's going on:** rates and percentages are hidden when fewer than 10 students are behind them.
  Counts by program, counts by term, and the student list are not hidden.
- **What to do:** before sharing outside your team, hide any group under 10 students, and the next
  smallest group too, so the hidden one can't be worked out by subtraction.
- **Also in:** [Playbook, Play 3](PLAYBOOK.md#play-3-see-who-is-close-to-finishing).

### Comparing with other tools

#### C14. The success measures and other tools ignore uploads

- **What you'll notice:** after an upload, the `near_completers` success measure, the equity gap
  finder and the AI data-definition tool still describe the sample data.
- **What's going on:** those tools read the files that ship with the project, not uploaded files.
  Only the dashboard (and `dashboard_counts.py`) follow uploads.
- **What to do:** don't compare their numbers with the dashboard after an upload.
- **Also in:** [Playbook, Play 7](PLAYBOOK.md#play-7-near-completers-as-a-measure).

### Privacy

#### C15. The hosted dashboard is open to anyone with the link

- **What's going on:** the dashboard has no sign-in. A hosted copy deployed to Vercel (see `docs/deploy.md`
  in pdp-near-completer-finder) opens to anyone who has its address, and so does its data
  service. Anything uploaded there can be seen by them. (The datathon's own hosted copy was checked
  on 2026-11-11, found open, and paused on 2026-11-24.)
- **What to do:** never upload real student records to a hosted copy. Add a sign-in before anyone
  does.
- **Also in:** [Upload runbook](RUNBOOK_UPLOADS.md#hosted-site-or-local-copy).
- **For developers:** on Vercel, deployment protection covers every deployment except custom
  domains, and the production `.vercel.app` domain answers publicly. Protect the production domain
  too, or put the app behind your college's sign-in.

---

## Not checked

### N1. Uploading on the hosted dashboard

- **What's going on:** every test of uploads was run on a local copy of the dashboard. No upload
  has been tried on a hosted copy. On Vercel, the dashboard saves uploads to a temporary folder
  that is **emptied whenever the hosting service starts a fresh copy** of the data service, so
  hosted uploads are expected to vanish after a while.
- **What to do:** do uploads on a local copy. Treat a hosted copy as showing the sample data.
- **Also in:** [Playbook, Play 5](PLAYBOOK.md#play-5-load-your-own-data) and
  [Upload runbook](RUNBOOK_UPLOADS.md#hosted-site-or-local-copy).
- **For developers:** the upload folder is `DASHBOARD_UPLOAD_DIR` (`/tmp/dashboard-uploads` in the
  API's production settings).

---

## Out-of-date documents

### D1. Old near-completer figures in the measures README

- **What's going on:** `measures/README.md` in the main project quotes 261 of 985 College 2 near
  completers. The current code gives 82 of 1,288.
- **What to do:** don't quote figures from that README. Rerun the measure (playbook, Play 7).
- **Also in:** [Playbook, Play 7](PLAYBOOK.md#play-7-near-completers-as-a-measure).
