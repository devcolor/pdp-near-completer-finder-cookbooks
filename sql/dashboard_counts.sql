-- The dashboard's executive numbers for one college, with the default filters (everything "all"/"any").
-- Mirrors pdp-near-completer-finder/playground/server_application/app/institution_dashboard/data.py.
-- Run it through scripts/dashboard_counts.py, which imports the CSVs into these tables and sets:
--   students_raw  students.csv, plus two columns the script adds: program, credits_remaining
--   profile       student_institutional_profile.csv
--   params        one row: threshold (0, 3, 6, 9, 12, 15 or 24, or NULL for the dashboard's default,
--                 "all stop-outs" with no credit band) and has_upload
--                 (1 when the folder read is <data root>/uploads/<college>, else 0)
-- Output: the view `output`, one row per number, as (section, item, value), in the order the API
-- returns them. Read it with: SELECT section, item, value FROM output ORDER BY s, o, item;
-- The data is synthetic unless a college uploaded its own. Nothing here is a finding about real students.

-- year_key(): a PDP year like "2024-25" sorts by its start year; anything else sorts as 0.
-- term_key(): "Fall 2024" sorts by year, then Spring 0 < Summer 1 < Fall 2; anything else sorts as 0.
-- Tables, not views, from here on: a large multi-year upload is slow to re-derive per row.
CREATE TEMP TABLE keyed AS
SELECT
  rowid AS file_order,
  *,
  trim(pdp_year) AS year,
  CASE WHEN substr(trim(pdp_year), 1, instr(trim(pdp_year) || '-', '-') - 1) GLOB '[0-9]*'
        AND substr(trim(pdp_year), 1, instr(trim(pdp_year) || '-', '-') - 1) NOT GLOB '*[^0-9]*'
       THEN CAST(substr(trim(pdp_year), 1, instr(trim(pdp_year) || '-', '-') - 1) AS INTEGER)
       ELSE 0 END AS year_key,
  trim("Last Enrolled Term") AS last_term,
  CASE WHEN length(trim("Last Enrolled Term")) - length(replace(trim("Last Enrolled Term"), ' ', '')) = 1
        AND substr(trim("Last Enrolled Term"), instr(trim("Last Enrolled Term"), ' ') + 1) GLOB '[0-9]*'
        AND substr(trim("Last Enrolled Term"), instr(trim("Last Enrolled Term"), ' ') + 1) NOT GLOB '*[^0-9]*'
       THEN CAST(substr(trim("Last Enrolled Term"), instr(trim("Last Enrolled Term"), ' ') + 1) AS INTEGER) * 10
            + CASE substr(trim("Last Enrolled Term"), 1, instr(trim("Last Enrolled Term"), ' ') - 1)
                WHEN 'Summer' THEN 1 WHEN 'Fall' THEN 2 ELSE 0 END
       ELSE 0 END AS term_key
FROM students_raw;

-- submitted_year_values(): the non-blank pdp_year values, newest last. Read from every row.
CREATE TEMP VIEW latest_year AS
SELECT year FROM keyed WHERE year <> '' ORDER BY year_key DESC, year DESC LIMIT 1;

-- is_multi_year(): an upload with two or more pdp_year values. Synthetic files never qualify.
CREATE TEMP VIEW mode AS
SELECT (SELECT has_upload FROM params) = 1 AND (SELECT count(DISTINCT year) FROM keyed WHERE year <> '') >= 2 AS multi_year;

-- _students(): one row per student, the newest pdp_year row (a tie goes to the later row in the file),
-- plus whether the student is absent from the newest year (absent_from_latest).
CREATE TEMP TABLE newest AS
SELECT r.*,
  p.has_any_year AND NOT p.in_latest AS absent_from_latest
FROM (SELECT k.*, row_number() OVER (PARTITION BY "Student GUID" ORDER BY year_key DESC, file_order DESC) AS pick
      FROM keyed k) r
JOIN (SELECT "Student GUID" AS guid,
             max(year <> '') AS has_any_year,
             max(year = (SELECT year FROM latest_year)) AS in_latest
      FROM keyed GROUP BY "Student GUID") p ON p.guid = r."Student GUID"
WHERE r.pick = 1;

-- build_dashboard(): in scope = not non-credit. CVC (excluded_from_outreach) is "left_out", the rest "measured".
CREATE TEMP TABLE in_scope AS
SELECT
  n."Student GUID" AS student_id,
  replace(n.program, ' (synthetic pathway)', '') AS program,  -- _label()
  CAST(trim(n.credits_remaining) AS REAL) AS credits_remaining,
  CAST(trim(n."Credits Applied to Program") AS REAL) AS credits_applied,
  n."Currently Enrolled" = 'Yes' AS enrolled,
  lower(trim(n.excluded_from_outreach)) = 'true' AS excluded,
  n.last_term, n.term_key, n.absent_from_latest
FROM newest n
WHERE n.student_type <> 'Non-credit (MASP included)';

CREATE TEMP VIEW measured AS SELECT * FROM in_scope WHERE NOT excluded;

-- _current_term(): the latest non-blank last term among in-scope students (CVC included).
CREATE TEMP TABLE current_term AS
SELECT last_term FROM in_scope WHERE last_term <> '' ORDER BY term_key DESC, last_term DESC LIMIT 1;

-- _is_near() (near_band): no threshold means any credits still owed; threshold 0 means no credits
-- applied yet; otherwise 0 < credits left <= threshold.
-- _left_with_credits(): credits still owed, and either absent from the newest year (multi-year)
-- or not currently enrolled (single year). Stop-out: left before the current term. Pending: left in it.
CREATE TEMP VIEW banded AS
SELECT m.*,
  CASE WHEN (SELECT threshold FROM params) IS NULL THEN m.credits_remaining > 0
       WHEN (SELECT threshold FROM params) = 0 THEN m.credits_applied = 0
       ELSE m.credits_remaining > 0 AND m.credits_remaining <= (SELECT threshold FROM params) END AS near_band,
  m.credits_remaining > 0
    AND CASE WHEN (SELECT multi_year FROM mode) THEN m.absent_from_latest ELSE NOT m.enrolled END AS left_with_credits,
  m.last_term = coalesce((SELECT last_term FROM current_term), '') AS in_current_term
FROM measured m;

-- build_dashboard()'s `near`: with no threshold (the default), every stop-out; otherwise near_band.
CREATE TEMP VIEW flagged AS
SELECT b.*,
  CASE WHEN (SELECT threshold FROM params) IS NULL THEN b.left_with_credits AND NOT b.in_current_term
       ELSE b.near_band END AS near
FROM banded b;

CREATE TEMP VIEW stopped AS SELECT * FROM flagged WHERE left_with_credits AND NOT in_current_term;

-- The output. _rate() hides count and n when n is under 10; so does this.
-- s and o are sort keys: order by s, o, item to get the API's order.
CREATE TEMP VIEW output AS
SELECT s, o, section, item, value FROM (
  SELECT 0 AS s, 0 AS o, 'meta' AS section, 'mode' AS item,
         CASE WHEN (SELECT multi_year FROM mode) THEN 'multi-year' ELSE 'single-year' END AS value
  UNION ALL SELECT 0, 1, 'meta', 'current_term', coalesce((SELECT last_term FROM current_term), '')
  UNION ALL SELECT 0, 2, 'meta', 'latest_pdp_year', coalesce((SELECT year FROM latest_year), '')
  UNION ALL SELECT 1, 0, 'summary', 'students', (SELECT count(*) FROM in_scope)
  UNION ALL SELECT 1, 1, 'summary', 'left_out', (SELECT count(*) FROM in_scope WHERE excluded)
  UNION ALL SELECT 1, 2, 'summary', 'near', (SELECT count(*) FROM flagged WHERE near)
  UNION ALL SELECT 1, 3, 'summary', 'stop_outs', (SELECT count(*) FROM stopped)
  UNION ALL SELECT 1, 4, 'summary', 'not_enrolled_this_term',
                   (SELECT count(*) FROM flagged WHERE left_with_credits AND in_current_term)
  UNION ALL SELECT 1, 5, 'summary', 'enrolled', (SELECT count(*) FROM measured WHERE enrolled)
  UNION ALL SELECT 2, 0, 'rates', 'stop_out_rate.count',
                   CASE WHEN (SELECT count(*) FROM measured) < 10 THEN NULL ELSE (SELECT count(*) FROM stopped) END
  UNION ALL SELECT 2, 1, 'rates', 'stop_out_rate.n',
                   CASE WHEN (SELECT count(*) FROM measured) < 10 THEN NULL ELSE (SELECT count(*) FROM measured) END
  UNION ALL SELECT 2, 2, 'rates', 'near_stop_out_rate.count',
                   CASE WHEN (SELECT count(*) FROM stopped) < 10 THEN NULL ELSE (SELECT count(*) FROM stopped WHERE near_band) END
  UNION ALL SELECT 2, 3, 'rates', 'near_stop_out_rate.n',
                   CASE WHEN (SELECT count(*) FROM stopped) < 10 THEN NULL ELSE (SELECT count(*) FROM stopped) END
  -- stop_outs: one row per term someone stopped out in, oldest first. Not suppressed in the app.
  UNION ALL SELECT * FROM (
    SELECT 3, min(term_key), 'stop_outs_by_term', last_term, count(*)
    FROM stopped GROUP BY last_term ORDER BY min(term_key), last_term)
  -- _program_counts(): `near` per program, largest first: near completers (enrolled or not) with a
  -- threshold, every stop-out without one. Not suppressed in the app.
  UNION ALL SELECT * FROM (
    SELECT 4, -count(*), 'program_counts', program, count(*)
    FROM flagged WHERE near GROUP BY program ORDER BY -count(*), program)
);
