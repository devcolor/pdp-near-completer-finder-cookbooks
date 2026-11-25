"""Tests for scripts/dashboard_counts.py on tiny made-up CSVs, so they never depend on the current data.

Expected numbers are worked out by hand from the dashboard's rules (data.py), not by running the SQL.
Run from the repo root: python -m unittest discover -s tests
"""

import contextlib
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from dashboard_counts import DataProblem, dashboard_counts, main  # noqa: E402

HEADER = ["Student GUID", "pdp_year", "student_type", "excluded_from_outreach", "Currently Enrolled",
          "Last Enrolled Term", "Credits Applied to Program", "Degree Program (Major)", "Units Remaining"]


def student(guid, enrolled, term, left, applied="10", year="2025-26", kind="Credit", cvc="", major="BIOLOGY"):
    """One students.csv row for CMC."""
    return [guid, year, kind, cvc, enrolled, term, applied, major, left]


# A: enrolled, 5 left.          B: left Spring 2025, 4 left (stop-out, near at 6).
# C: left Fall 2025, 20 left (stop-out, not near).  D: left in Fall 2026, the current term (pending).
# E: non-credit (out of scope). F: CVC (left out).  G: not enrolled, nothing left (finished, not a stop-out).
SINGLE_YEAR = [
    student("A", "Yes", "Fall 2026", "5"),
    student("B", "No", "Spring 2025", "4", year="2024-25"),
    student("C", "No", "Fall 2025", "20"),
    student("D", "No", "Fall 2026", "3", applied="0"),
    student("E", "No", "Spring 2024", "2", kind="Non-credit (MASP included)"),
    student("F", "No", "Spring 2024", "2", cvc="True"),
    student("G", "No", "Spring 2025", "0", year="2024-25"),
]


def write(folder: Path, students, header=HEADER, profile_ids=None, bom=False):
    """Write students.csv and student_institutional_profile.csv into folder."""
    folder.mkdir(parents=True, exist_ok=True)
    encoding = "utf-8-sig" if bom else "utf-8"
    with (folder / "students.csv").open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(students)
    ids = profile_ids if profile_ids is not None else sorted({row[header.index("Student GUID")] for row in students})
    with (folder / "student_institutional_profile.csv").open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["student_id", "is_parent"])
        writer.writerows([guid, "False"] for guid in ids)


class DashboardCountsTest(unittest.TestCase):
    """dashboard_counts() against hand-worked answers."""

    def setUp(self):
        """A fresh data root per test."""
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        """Remove the data root."""
        self._tmp.cleanup()

    def summary(self, result):
        """The summary section as a dict."""
        return {row["item"]: row["value"] for row in result.rows if row["section"] == "summary"}

    def test_single_year(self):
        """Base files: stop-outs by enrollment flag, pending in the current term, scope and CVC rules."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        result = dashboard_counts("cmc", 6, self.root)
        self.assertFalse(result.has_upload)
        self.assertEqual(result.value("meta", "mode"), "single-year")
        self.assertEqual(result.value("meta", "current_term"), "Fall 2026")
        self.assertEqual(self.summary(result), {
            "students": 6, "left_out": 1, "near": 3, "stop_outs": 2,
            "not_enrolled_this_term": 1, "enrolled": 1,
        })
        by_term = [(row["item"], row["value"]) for row in result.rows if row["section"] == "stop_outs_by_term"]
        self.assertEqual(by_term, [("Spring 2025", 1), ("Fall 2025", 1)])
        # Rates are hidden under 10 students, as _rate() does.
        self.assertIsNone(result.value("rates", "stop_out_rate.count"))

    def test_default_is_every_stop_out(self):
        """With no credit band (the dashboard's default), "near" is every stop-out: B and C."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        result = dashboard_counts("cmc", data_dir=self.root)
        self.assertEqual(result.threshold, "stop_outs")
        self.assertEqual(self.summary(result)["near"], 2)
        self.assertEqual(result.value("program_counts", "BIOLOGY"), 2)
        self.assertEqual(self.summary(dashboard_counts("cmc", "9", self.root))["near"], 3)  # digits as text work too

    def test_threshold_zero_means_no_credits_applied(self):
        """Threshold 0 counts students with nothing applied to the program, not 0 credits left."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        self.assertEqual(self.summary(dashboard_counts("cmc", 0, self.root))["near"], 1)  # only D

    def test_several_years_in_base_files_stay_single_year(self):
        """Only an upload can switch to the multi-year rule, as is_multi_year() requires."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        result = dashboard_counts("cmc", 6, self.root)
        self.assertEqual(result.pdp_years, ["2024-25", "2025-26"])
        self.assertEqual(result.value("meta", "mode"), "single-year")

    def test_upload_with_two_years_counts_absence(self):
        """An upload with two years: a stop-out is missing from the newest year and still owes credits."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        uploads = self.root / "elsewhere"
        write(uploads / "cmc", [
            student("A", "Yes", "Spring 2025", "8", year="2024-25"),
            student("A", "Yes", "Spring 2026", "5", year="2025-26"),  # newest row wins: 5 left
            student("B", "Yes", "Spring 2025", "4", year="2024-25"),  # gone from 2025-26: stop-out
            student("C", "Yes", "Spring 2025", "0", year="2024-25"),  # gone, nothing left: finished
        ])
        result = dashboard_counts("cmc", 6, self.root, upload_dir=uploads)
        self.assertTrue(result.has_upload)
        self.assertEqual(result.value("meta", "mode"), "multi-year")
        self.assertEqual(result.value("meta", "latest_pdp_year"), "2025-26")
        summary = self.summary(result)
        self.assertEqual((summary["students"], summary["stop_outs"], summary["near"]), (3, 1, 2))

    def test_upload_folder_defaults_to_uploads_in_data_root(self):
        """Without an upload folder, <data root>/uploads is used, as in local development."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        write(self.root / "uploads" / "cmc", [student("Z", "Yes", "Spring 2026", "5")])
        result = dashboard_counts("cmc", 6, self.root)
        self.assertTrue(result.has_upload)
        self.assertEqual(self.summary(result)["students"], 1)

    def test_byte_order_mark_and_reordered_columns(self):
        """A BOM in front of a reordered header still reads, as the app's utf-8-sig reader does."""
        header = HEADER[::-1]
        rows = [row[::-1] for row in SINGLE_YEAR]
        write(self.root / "cmc" / "csv", rows, header=header, bom=True)
        self.assertEqual(self.summary(dashboard_counts("cmc", 6, self.root))["stop_outs"], 2)

    def test_refuses_what_the_app_refuses_or_fails_on(self):
        """Bad threshold, missing column, blank credits and a missing profile row are named."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        with self.assertRaisesRegex(DataProblem, "threshold must be stop_outs or one of"):
            dashboard_counts("cmc", 7, self.root)

        write(self.root / "cmc" / "csv", [row[:-1] for row in SINGLE_YEAR], header=HEADER[:-1])
        with self.assertRaisesRegex(DataProblem, 'missing column "Units Remaining"'):
            dashboard_counts("cmc", 6, self.root)

        write(self.root / "cmc" / "csv", SINGLE_YEAR + [student("H", "No", "Spring 2025", "")])
        with self.assertRaisesRegex(DataProblem, r'1 row\(s\) with a blank or non-numeric "Units Remaining"'):
            dashboard_counts("cmc", 6, self.root)

        write(self.root / "cmc" / "csv", SINGLE_YEAR, profile_ids=["A", "B"])
        with self.assertRaisesRegex(DataProblem, r"5 student\(s\) with no row"):
            dashboard_counts("cmc", 6, self.root)

    def test_command_line_exit_codes(self):
        """0 when it works, 1 on a data problem."""
        write(self.root / "cmc" / "csv", SINGLE_YEAR)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["cmc", "6", "--data-dir", str(self.root), "--csv"]), 0)
            self.assertEqual(main(["cmc", "7", "--data-dir", str(self.root)]), 1)


if __name__ == "__main__":
    unittest.main()
