"""The dashboard's executive numbers for one college, worked out from the CSVs.

Reads the same folder the app reads (a saved upload first, else the base files), loads the CSVs into
an in-memory SQLite database, and runs sql/dashboard_counts.sql, which mirrors build_dashboard in
gia-datathon/playground/server_application/app/institution_dashboard/data.py.

Command line:
    python scripts/dashboard_counts.py <cmc|college_two> [threshold] [--data-dir DIR] [--upload-dir DIR] [--csv]

    threshold is stop_outs (the dashboard's default: every stop-out, no credit band) or one of
    0, 3, 6, 9, 12, 15, 24 (a credit band; 0 means no credits applied to the program yet).

From Python (a notebook, for example):
    import sys; sys.path.append("<path to gia-datathon-cookbooks>/scripts")
    from dashboard_counts import dashboard_counts
    result = dashboard_counts("cmc")         # the dashboard's default, or dashboard_counts("cmc", 9)
    result.rows        # list of {"section", "item", "value"} dicts: pandas.DataFrame(result.rows)

Python 3.10 or newer, standard library only. The bundled data is synthetic: nothing it prints is a
finding about real students or institutions.
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

# THRESHOLDS in data.py; the API answers 422 to anything else.
THRESHOLDS = (0, 3, 6, 9, 12, 15, 24)
# PATHWAY_ALL in data.py: the default credit filter, every stop-out with no credit band.
ALL_STOP_OUTS = "stop_outs"
SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "dashboard_counts.sql"
# The college's columns, as _students() in data.py names them.
COLUMNS = {
    "college_two": {"program": "Target Program", "credits": "Credits Remaining"},
    "cmc": {"program": "Degree Program (Major)", "credits": "Units Remaining"},
}


class DataProblem(Exception):
    """A problem with the folder or the files that stops the numbers from being worked out."""


@dataclass
class Result:
    """The numbers for one college, and which data they came from."""

    college: str
    threshold: int | str
    folder: Path
    has_upload: bool
    pdp_years: list[str]
    rows: list[dict] = field(default_factory=list)

    def value(self, section: str, item: str):
        """One number, such as value("summary", "stop_outs"), or None if it isn't there."""
        for row in self.rows:
            if row["section"] == section and row["item"] == item:
                return row["value"]
        return None


def default_data_dir() -> Path:
    """$DASHBOARD_DATA_DIR, else the synthetic data in $GIA_REPO or the gia-datathon repo next to this one."""
    if os.environ.get("DASHBOARD_DATA_DIR"):
        return Path(os.environ["DASHBOARD_DATA_DIR"])
    repo = Path(os.environ.get("GIA_REPO") or Path(__file__).resolve().parent.parent.parent / "gia-datathon")
    return repo / "gia-pre-implementation" / "synthetic-datasets"


def find_folder(college: str, data_dir: Path, upload_dir: Path | None) -> tuple[Path, bool]:
    """The folder the app reads for this college, and whether it is a saved upload.

    Mirrors institution_folder() in data.py: a saved upload wins over the base files. Uploads live in
    DASHBOARD_UPLOAD_DIR when the app sets it (production uses /tmp/dashboard-uploads).
    """
    upload_dir = upload_dir or data_dir / "uploads"
    if (upload_dir / college / "students.csv").is_file():
        return upload_dir / college, True
    return data_dir / college / "csv", False


def _load_csv(connection: sqlite3.Connection, table: str, path: Path) -> None:
    """Load one CSV into a table of text columns, named by its header.

    utf-8-sig drops a byte-order mark, as the app's reader does. Short rows are padded with NULL.
    """
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        if not header:
            raise DataProblem(f"{path} has no header row")
        quoted = ", ".join('"' + name.replace('"', '""') + '"' for name in header)
        connection.execute(f"CREATE TABLE {table} ({quoted})")
        width = len(header)
        rows = ((row + [None] * width)[:width] for row in reader if row)
        connection.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * width)})", rows)


def _check(connection: sqlite3.Connection, program: str, credits: str) -> None:
    """Raise DataProblem for anything that would make the app fail, before printing any number."""
    needed = {
        "students_raw": ["Student GUID", "pdp_year", "student_type", "excluded_from_outreach",
                         "Currently Enrolled", "Last Enrolled Term", "Credits Applied to Program",
                         program, credits],
        "profile": ["student_id"],
    }
    file_of = {"students_raw": "students.csv", "profile": "student_institutional_profile.csv"}
    for table, columns in needed.items():
        present = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        missing = [column for column in columns if column not in present]
        if missing:
            raise DataProblem("\n".join(f'missing column "{column}" in {file_of[table]}' for column in missing))

    # Values the app's float() would reject. Checks every row, so it can flag an older-year row too.
    problems = []
    for column in (credits, "Credits Applied to Program"):
        quoted = '"' + column.replace('"', '""') + '"'
        (bad,) = connection.execute(
            f"SELECT count(*) FROM students_raw WHERE {quoted} IS NULL OR trim({quoted}) = '' "
            f"OR trim({quoted}) GLOB '*[^0-9.eE+-]*'"
        ).fetchone()
        if bad:
            problems.append(
                f'{bad} row(s) with a blank or non-numeric "{column}" (the dashboard returns 422 on these)'
            )
    (orphans,) = connection.execute(
        'SELECT count(DISTINCT "Student GUID") FROM students_raw '
        'WHERE "Student GUID" NOT IN (SELECT student_id FROM profile WHERE student_id IS NOT NULL)'
    ).fetchone()
    if orphans:
        problems.append(
            f"{orphans} student(s) with no row in student_institutional_profile.csv (the dashboard fails on these)"
        )
    if problems:
        raise DataProblem("\n".join(problems))


def parse_threshold(threshold: int | str) -> int | None:
    """The credit band for a threshold, or None for all stop-outs. Mirrors parse_credits() in data.py."""
    if threshold == ALL_STOP_OUTS:
        return None
    if isinstance(threshold, str) and threshold.isdigit():
        threshold = int(threshold)
    if isinstance(threshold, int) and threshold in THRESHOLDS:
        return threshold
    raise DataProblem(
        f"threshold must be {ALL_STOP_OUTS} or one of {' '.join(map(str, THRESHOLDS))} (got {threshold})"
    )


def dashboard_counts(
    college: str,
    threshold: int | str = ALL_STOP_OUTS,
    data_dir: str | Path | None = None,
    upload_dir: str | Path | None = None,
) -> Result:
    """Work out the dashboard's executive numbers for one college. Raises DataProblem on bad input."""
    if college not in COLUMNS:
        raise DataProblem(f"college must be cmc or college_two (got {college})")
    band = parse_threshold(threshold)
    data_dir = Path(data_dir) if data_dir else default_data_dir()
    if upload_dir is None and os.environ.get("DASHBOARD_UPLOAD_DIR"):
        upload_dir = os.environ["DASHBOARD_UPLOAD_DIR"]
    upload_dir = Path(upload_dir) if upload_dir else None
    if not data_dir.is_dir():
        raise DataProblem(
            f"data folder not found: {data_dir} (set GIA_REPO, DASHBOARD_DATA_DIR or --data-dir)"
        )

    folder, has_upload = find_folder(college, data_dir, upload_dir)
    for name in ("students.csv", "student_institutional_profile.csv"):
        if not (folder / name).is_file():
            raise DataProblem(f"missing {folder / name}")

    names = COLUMNS[college]
    connection = sqlite3.connect(":memory:")
    try:
        _load_csv(connection, "students_raw", folder / "students.csv")
        _load_csv(connection, "profile", folder / "student_institutional_profile.csv")
        _check(connection, names["program"], names["credits"])
        years = [row[0] for row in connection.execute(
            "SELECT DISTINCT trim(pdp_year) FROM students_raw WHERE trim(pdp_year) <> '' ORDER BY 1"
        )]
        program = '"' + names["program"].replace('"', '""') + '"'
        credits = '"' + names["credits"].replace('"', '""') + '"'
        connection.executescript(
            "ALTER TABLE students_raw ADD COLUMN program TEXT;"
            "ALTER TABLE students_raw ADD COLUMN credits_remaining TEXT;"
            f"UPDATE students_raw SET program = {program}, credits_remaining = {credits};"
        )
        connection.execute("CREATE TABLE params (threshold INTEGER, has_upload INTEGER)")
        connection.execute("INSERT INTO params VALUES (?, ?)", (band, int(has_upload)))
        connection.executescript(SQL_FILE.read_text())
        rows = [
            {"section": section, "item": item, "value": value}
            for section, item, value in connection.execute(
                "SELECT section, item, value FROM output ORDER BY s, o, item"
            )
        ]
    finally:
        connection.close()
    return Result(college, threshold, folder, has_upload, years, rows)


def _print_table(result: Result) -> None:
    """Print the numbers for a person to read, with which data they came from."""
    print(f"Folder:     {result.folder}")
    print(f"Upload:     {'yes' if result.has_upload else 'no (synthetic files)'}")
    print(f"pdp_year:   {', '.join(result.pdp_years) or 'none'}")
    print(f"Threshold:  {result.threshold}")
    widths = [max(len(str(row[key] if row[key] is not None else "")) for row in result.rows + [
        {"section": "section", "item": "item", "value": "value"}]) for key in ("section", "item", "value")]
    line = "  ".join(f"{{:<{width}}}" for width in widths)
    print(line.format("section", "item", "value"))
    print(line.format(*("-" * width for width in widths)))
    for row in result.rows:
        print(line.format(row["section"], row["item"], "" if row["value"] is None else row["value"]))


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point. Returns the exit code: 0 done, 1 data problem, 2 usage."""
    parser = argparse.ArgumentParser(
        prog="dashboard_counts.py",
        description="The dashboard's executive numbers for one college, from the CSVs the app reads.",
    )
    parser.add_argument("college", choices=sorted(COLUMNS))
    parser.add_argument("threshold", nargs="?", default=ALL_STOP_OUTS,
                        help="stop_outs (default, as the dashboard: every stop-out) or 0, 3, 6, 9, 12, 15, 24")
    parser.add_argument("--data-dir", help="the app's data root; default $DASHBOARD_DATA_DIR, else the synthetic data")
    parser.add_argument("--upload-dir", help="where the app saves uploads; default $DASHBOARD_UPLOAD_DIR, else <data-dir>/uploads")
    parser.add_argument("--csv", action="store_true", help="print section,item,value lines")
    args = parser.parse_args(argv)
    try:
        result = dashboard_counts(args.college, args.threshold, args.data_dir, args.upload_dir)
    except DataProblem as problem:
        print(f"dashboard_counts: {problem}", file=sys.stderr)
        return 1
    if args.csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerows((row["section"], row["item"], "" if row["value"] is None else row["value"])
                         for row in result.rows)
    else:
        _print_table(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
