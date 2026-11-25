"""Check that dashboard_counts.py and a running dashboard API give the same numbers.

Only meaningful when both read the same data: a local API, and the same data root and upload folder
(pass --data-dir and --upload-dir with the absolute paths the API's DASHBOARD_DATA_DIR and
DASHBOARD_UPLOAD_DIR point to, if they are set).

Command line:
    python scripts/verify_against_api.py <cmc|college_two> [threshold] [--api URL] [--data-dir DIR] [--upload-dir DIR]

From Python:
    from verify_against_api import compare
    differences = compare("cmc")             # [] when everything matches; compare("cmc", 9) for a band

Exit code 0 when every number matches, 1 on any difference or when the API can't be read, 2 on bad
arguments. Python 3.10 or newer, standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_counts import COLUMNS, DataProblem, dashboard_counts  # noqa: E402

DEFAULT_API = "http://localhost:8000/api/v1"


def api_numbers(body: dict) -> dict[tuple[str, str], object]:
    """The API's numbers, keyed the way dashboard_counts.sql names them."""
    numbers = {("summary", row["id"]): row["value"] for row in body["summary"]}
    for row in body["rates"]:
        numbers[("rates", row["id"] + ".count")] = row["count"]
        numbers[("rates", row["id"] + ".n")] = row["n"]
    numbers[("meta", "current_term")] = body["current_term"]
    for row in body["stop_outs"]:
        numbers[("stop_outs_by_term", row["term"])] = row["stop_outs"]
    for row in body["program_counts"]:
        numbers[("program_counts", row["program"])] = row["count"]
    return numbers


def fetch(api: str, college: str, threshold: int | str) -> dict:
    """The API's /dashboard response for one college and threshold. Raises OSError if unreachable."""
    url = f"{api}/dashboard?institution={college}&credit_threshold={threshold}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def compare(
    college: str,
    threshold: int | str = "stop_outs",
    api: str = DEFAULT_API,
    data_dir: str | Path | None = None,
    upload_dir: str | Path | None = None,
) -> list[str]:
    """Every number that differs between the API and dashboard_counts, as readable lines. [] means all match."""
    return differences(fetch(api, college, threshold), dashboard_counts(college, threshold, data_dir, upload_dir))


def differences(body: dict, result) -> list[str]:
    """Compare one API response with one dashboard_counts result."""
    ours = {
        (row["section"], row["item"]): row["value"]
        for row in result.rows
        if not (row["section"] == "meta" and row["item"] in ("mode", "latest_pdp_year"))
    }
    theirs = api_numbers(body)
    return [
        f"  {section} / {item}: api={theirs.get((section, item))!r} sql={ours.get((section, item))!r}"
        for section, item in sorted(set(theirs) | set(ours))
        if theirs.get((section, item), "missing") != ours.get((section, item), "missing")
    ]


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(
        prog="verify_against_api.py",
        description="Compare dashboard_counts.py with a running dashboard API.",
    )
    parser.add_argument("college", choices=sorted(COLUMNS))
    parser.add_argument("threshold", nargs="?", default="stop_outs",
                        help="stop_outs (default, as the dashboard) or 0, 3, 6, 9, 12, 15, 24")
    parser.add_argument("--api", default=DEFAULT_API, help=f"the API's /api/v1 base (default {DEFAULT_API})")
    parser.add_argument("--data-dir")
    parser.add_argument("--upload-dir")
    args = parser.parse_args(argv)

    url = f"{args.api}/dashboard?institution={args.college}&credit_threshold={args.threshold}"
    try:
        body = fetch(args.api, args.college, args.threshold)
        result = dashboard_counts(args.college, args.threshold, args.data_dir, args.upload_dir)
    except DataProblem as problem:
        print(f"dashboard_counts: {problem}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:  # the API is down, or answered with an error or bad JSON
        print(f"verify: could not read {url}: {error}", file=sys.stderr)
        return 1

    numbers = len(api_numbers(body))
    ours = sum(1 for row in result.rows if not (row["section"] == "meta" and row["item"] in ("mode", "latest_pdp_year")))
    print(f"{numbers} API numbers, {ours} SQL numbers, stop-out rule: {result.value('meta', 'mode')}, "
          f"upload in use (API): {body.get('using_upload')}")
    found = differences(body, result)
    if found:
        print("DIFFERENT:\n" + "\n".join(found))
        return 1
    print("All match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
