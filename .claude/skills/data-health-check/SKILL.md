---
name: data-health-check
description: Check the data the GIA stop-out dashboard is reading, and explain the result in plain language. Runs python3 scripts/dashboard_counts.py and, if a dashboard API is reachable, scripts/verify_against_api.py. Use when someone asks whether an upload is OK, which data the dashboard is using, how stop-outs are being counted, why the dashboard shows an error, or whether the dashboard matches the data.
---

# data-health-check

Run the cookbook's read-only checks, then explain what they found to someone who may not be an
engineer.

This skill depends on `scripts/dashboard_counts.py`, `scripts/verify_against_api.py` and
`sql/dashboard_counts.sql`. If they are missing, say the scripts were removed and stop. Don't
rebuild them.

## Steps

1. **Ask only what you can't infer:**
   - **College:** `cmc` (Copper Mountain), `college_two` (College 2), or both. The default is both.
   - **Credit filter:** `stop_outs` (the default, as on the dashboard: every stop-out) or 0, 3, 6,
     9, 12, 15, 24.
   - **Data folders:** only if the dashboard runs with `DASHBOARD_DATA_DIR` or `DASHBOARD_UPLOAD_DIR`.
     Pass the same absolute paths with `--data-dir` and `--upload-dir`.

2. **Run the counts,** from the root of this repo:

   ```bash
   python3 scripts/dashboard_counts.py <college> <threshold> [--data-dir DIR] [--upload-dir DIR]
   ```

   If it stops with a message, that message is the finding. Go to step 4.

3. **Compare with the dashboard,** if one is reachable:
   - Local: `curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/dashboard`.
     If that answers `200`, run `python3 scripts/verify_against_api.py <college> <threshold> [--data-dir DIR] [--upload-dir DIR]`.
   - Hosted: only when the person asks about the hosted site, run it with
     `--api https://<your-api>/api/v1` (the hosted API's address). This compares the hosted site with the
     **local** files, so it means something only while the hosted site shows the sample data and
     the local files are the sample data.

4. **Explain in plain language,** in this order:
   - **Which data:** uploaded files or the sample data, the academic years present (`pdp_year`),
     and the current term.
   - **How stop-outs are counted:** single-year means "not enrolled and still owes credits".
     Multi-year means "missing from the newest year and still owes credits"
     ([C4](../../../KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted)).
   - **The headline:** students, near completers, stop-outs, not enrolled this term.
   - **Problems:** map each script message to its known issue:

     | Script says | Known issue |
     | --- | --- |
     | blank or non-numeric credits | B2 |
     | student(s) with no row in the profile file | B3 |
     | missing column | Fix the file. The upload page would also reject it |
     | `verify` shows differences | The dashboard and the files differ: a different data folder, or the app changed |

   - **What to do next.** Link to `KNOWN_ISSUES.md` and `RUNBOOK_UPLOADS.md` entries by ID.

## Rules

- Read-only. Never upload, delete, or edit data files in this skill.
- Never show student IDs or names. The scripts don't print any; don't query for them.
- Don't share counts by program or by term outside the team when a group has fewer than 10
  students ([C13](../../../KNOWN_ISSUES.md#c13-small-groups-are-not-always-hidden)). Summarize
  instead.
- Course-related checks aren't covered: the scripts check student counts, not course history
  ([B1](../../../KNOWN_ISSUES.md#b1-uploading-course-history-throws-most-of-it-away),
  [B4](../../../KNOWN_ISSUES.md#b4-course-drop-and-fail-rates-ignore-uploads)).
- Say the data is synthetic when it is the bundled sample data.
