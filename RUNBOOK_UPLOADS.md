# Runbook: changing the dashboard's data by uploading CSV files

For people who know the students and programs but don't write software: advisors, deans and
institutional researchers. You need a web browser and the four CSV files. You don't need to run any
commands.

> **Read first.** Uploads have never been tested on the hosted dashboard (see
> [Hosted site or local copy](#hosted-site-or-local-copy)). Never upload real student records to the
> hosted dashboard: anyone with the link can see it, with no sign-in
> ([C15](KNOWN_ISSUES.md#c15-the-hosted-dashboard-is-open-to-anyone-with-the-link)).

## What an upload does

The dashboard keeps four files for each college:

| File | What it holds |
| --- | --- |
| `students.csv` | One row per student per academic year: program, credits, enrollment, last term |
| `student_institutional_profile.csv` | One row per student: holds, parenting, work, housing |
| `course_schedule.csv` | When and where courses are offered |
| `course_detail.csv` | Every course each student took, with grades |

An upload replaces some or all of what the dashboard has for **one** college. The other college
isn't touched. Until anyone uploads, the dashboard shows made-up sample data.

## Hosted site or local copy

| | Hosted dashboard | Local copy (on a teammate's computer) |
| --- | --- | --- |
| Address | Your deployment's address, such as `https://<your-web-app>.vercel.app/dashboard/upload` | http://localhost:3000/dashboard/upload |
| Who can see it | **Anyone with the link, with no sign-in** (checked 2026-11-11) | Only that computer |
| Do uploads work? | **Not tested.** An upload may fail with an error, or seem to work and then disappear later | Yes, tested |
| Real student data? | **No** | Only if your college's data rules allow that computer |

Until a technical teammate confirms that hosted uploads work and the site is protected, do uploads
on a local copy. Ask a teammate to start one (playbook, Play 1).

## Before you upload: checklist

Go through each item. Each one prevents a known problem.

- [ ] **All four files are ready.** The page won't save fewer than four.
- [ ] **Every file has the columns the page lists.** The page shows "Required columns" under each
  file. Extra columns are fine, and missing ones are rejected.
- [ ] **Files are saved as CSV in UTF-8, each 15 MB or smaller.** In Excel: *File > Save As > CSV
  UTF-8*.
- [ ] **Every row of `students.csv` has a `pdp_year`,** written like `2024-25`. Fall starts the
  academic year: Fall 2024 and Spring 2025 are both `2024-25`.
- [ ] **Each academic year in your file is complete:** Fall, Spring and Summer students together.
  Uploading a year replaces everything saved for that year
  ([C2](KNOWN_ISSUES.md#c2-uploading-a-year-replaces-that-whole-year)).
- [ ] **If this is the first upload for this college, the file holds every year you want to keep.**
  The first upload replaces the sample data instead of adding to it
  ([C1](KNOWN_ISSUES.md#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it)).
- [ ] **The profile file has a row for every student in every year you've uploaded,** not only the
  new ones. A missing student breaks the dashboard
  ([B3](KNOWN_ISSUES.md#b3-a-student-with-no-profile-row-breaks-the-dashboard)).
- [ ] **No blank credits.** Every student has a number for credits remaining and credits applied
  ([B2](KNOWN_ISSUES.md#b2-a-blank-credits-value-gives-a-misleading-error)).
- [ ] **Terms are written like `Fall 2024`, `Spring 2025` or `Summer 2025`**
  ([C8](KNOWN_ISSUES.md#c8-term-names-must-be-written-one-way)).
- [ ] **Credits remaining are up to date.** The dashboard uses them exactly as given and never
  recalculates them from courses
  ([C6](KNOWN_ISSUES.md#c6-credits-remaining-are-used-exactly-as-uploaded)).
- [ ] **You accept that some course details will be wrong.** An upload currently keeps only part of
  the course history file. Attempt counts and "next offered" will be wrong
  ([B1](KNOWN_ISSUES.md#b1-uploading-course-history-throws-most-of-it-away)), and the "high DFW"
  course flags keep describing the sample data
  ([B4](KNOWN_ISSUES.md#b4-course-drop-and-fail-rates-ignore-uploads)). Student counts, near
  completers, stop-outs, and the list of courses each student still owes are not affected.

## Upload

1. Open the Upload page (the address is in the table above).
2. Pick the college in the drop-down: **Copper Mountain** or **College 2**.
3. Under each of the four file names, click **Choose file** and pick that file. The file name
   appears next to the button.
4. Click **Check and save**.
   - **If it works,** the page saves the files, and "Years submitted" lists the years it now holds.
   - **If it says "Upload failed",** read the message. It names the missing column, the oversized
     file, or the rows without a `pdp_year`. Nothing was saved, so the dashboard still has what it
     had. Fix the file and try again.

## After you upload: check these three things

1. **Years submitted** (on the Upload page): are the right years listed, with sensible student
   counts?
2. **"Counting stop-outs by:"** (on the Upload page). This changes once two or more years are saved,
   and stop-out counts can jump when it does
   ([C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted)):
   - one year: "Not enrolled, with credits still left on the major"
   - two or more years: "Absent from *newest year*, the most recent year submitted"
3. **The executive view** loads without an error. If it says "unknown filter" or "Something went
   wrong", see [What went wrong](#what-went-wrong).

Remember: on screen, terms are labeled by calendar year. Fall 2024 shows as "24 Fall" and Spring
2025 as "25 Spring", though both are in your file's `2024-25` year
([C9](KNOWN_ISSUES.md#c9-term-labels-use-the-calendar-year-not-the-academic-year)).

## Undo

| To | Do |
| --- | --- |
| Take one year back out | On the Upload page, under "Years submitted", click **Remove** next to that year |
| Go back to the sample data for this college | Click **Restore synthetic files**. This deletes everything uploaded for that college |

These buttons appear only while the college is using uploaded files.

## What went wrong

| You see | Likely cause | What to do |
| --- | --- | --- |
| "Upload failed" naming a column | A file is missing a required column | Add the column and upload again |
| "Upload failed" mentioning `pdp_year` | Some rows of `students.csv` have no year | Fill in `pdp_year` on every row |
| "Upload failed", larger than 15 MB | The file is too big | Split it by year and upload one year at a time |
| The dashboard says "Unknown filter for this institution" | A blank or non-number credits value ([B2](KNOWN_ISSUES.md#b2-a-blank-credits-value-gives-a-misleading-error)) | Fix the credits columns, upload again |
| The dashboard says "Something went wrong on our side" | A student is missing from the profile file ([B3](KNOWN_ISSUES.md#b3-a-student-with-no-profile-row-breaks-the-dashboard)) | Upload a profile file that covers every student |
| Far fewer students than before | This was the first upload, and it replaced the sample data ([C1](KNOWN_ISSUES.md#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it)) | Expected. Upload the other years too, or restore |
| Stop-outs jumped | A second year switched the counting rule ([C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted)) | Expected. Check that the newest year is complete |
| On the hosted site, the upload worked but later vanished | Hosted uploads aren't supported or tested ([N1](KNOWN_ISSUES.md#n1-uploading-on-the-hosted-dashboard)) | Use a local copy |

A technical teammate can run the `data-health-check` skill, or `scripts/dashboard_counts.py`, to
find the exact rows behind most of these problems ([Toolbox](TOOLBOX.md)).
