"""One free, manual check that the cookbook still matches the dashboard. Run it before sharing the
cookbook, and after pdp-near-completer-finder changes.

    python3 scripts/check_cookbook.py                       # against a local copy (localhost:8000)
    python3 scripts/check_cookbook.py --api https://<your-api>/api/v1   # or a hosted copy

It checks this repo (unit tests, links, the two skill copies) and what the docs say about the
dashboard (the default credit filter, the accepted credit choices, how terms are labeled, the
documented filters, and the numbers themselves). It only reads: nothing is uploaded or changed.
Every line says PASS, FAIL, SKIP or INFO. The exit code is 1 if anything failed.

Python 3.10 or newer, standard library only.
"""

from __future__ import annotations

import argparse
import filecmp
import io
import json
import os
import re
import subprocess
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from dashboard_counts import ALL_STOP_OUTS, THRESHOLDS, DataProblem, default_data_dir  # noqa: E402
from verify_against_api import compare  # noqa: E402

DEFAULT_API = "http://localhost:8000/api/v1"
SEASONS = ("Spring", "Summer", "Fall")


class Report:
    """Collects PASS / FAIL / SKIP / INFO lines and prints them as they come."""

    def __init__(self):
        """Start with nothing failed."""
        self.failed = 0

    def line(self, status: str, name: str, detail: str = "") -> None:
        """Print one result line, and count failures."""
        self.failed += status == "FAIL"
        print(f"{status:<4}  {name}" + (f": {detail}" if detail else ""))

    def check(self, ok: bool, name: str, detail_if_failed: str, detail_if_passed: str = "") -> None:
        """PASS or FAIL, depending on ok."""
        self.line("PASS" if ok else "FAIL", name, detail_if_passed if ok else detail_if_failed)


def term_label_problems(terms: list[dict]) -> list[str]:
    """Terms whose on-screen label isn't "<2-digit calendar year> <season>", which is what C9 documents."""
    problems = []
    for term in terms:
        season, _, year = term["value"].partition(" ")
        expected = f"{int(year) % 100:02d} {season}" if year.isdigit() and season in SEASONS else None
        if expected is not None and term["label"] != expected:
            problems.append(f'{term["value"]} shows as "{term["label"]}", docs say "{expected}"')
    return problems


def broken_links(root: Path) -> list[str]:
    """Relative Markdown links and #anchors under root that don't resolve. Text in backticks is skipped."""

    def slug(heading: str) -> str:
        """GitHub's anchor for a heading."""
        return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")

    files = [path for path in root.rglob("*.md") if ".git" not in path.parts]
    anchors = {path.resolve(): {slug(h) for h in re.findall(r"^#+ (.+)$", path.read_text(), re.M)} for path in files}
    problems = []
    for path in files:
        text = re.sub(r"`[^`\n]*`", "", path.read_text())
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, fragment = target.partition("#")
            destination = (path.parent / file_part).resolve() if file_part else path.resolve()
            if not destination.exists():
                problems.append(f"{path.relative_to(root)} -> {target} (no such file)")
            elif fragment and destination in anchors and fragment not in anchors[destination]:
                problems.append(f"{path.relative_to(root)} -> {target} (no such heading)")
    return problems


def different_skill_files(root: Path) -> list[str]:
    """Files that differ, or exist on one side only, between .claude/skills and .agents/skills."""
    found = []

    def walk(comparison: filecmp.dircmp, prefix: str) -> None:
        """Record differences in this folder and its subfolders."""
        found.extend(prefix + name for name in comparison.left_only + comparison.right_only + comparison.diff_files)
        for name, sub in comparison.subdirs.items():
            walk(sub, f"{prefix}{name}/")

    walk(filecmp.dircmp(root / ".claude" / "skills", root / ".agents" / "skills", ignore=["__pycache__"]), "")
    return found


def get(api: str, path: str) -> tuple[int, dict | None]:
    """GET api+path. Returns the status code and the JSON body (None if the body isn't JSON)."""
    try:
        with urllib.request.urlopen(api + path, timeout=60) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, None


def checked_commit(root: Path) -> str | None:
    """The pdp-near-completer-finder commit the README says the cookbook was last checked against."""
    match = re.search(r"Last checked against pdp-near-completer-finder commit `([0-9a-f]+)`", (root / "README.md").read_text())
    return match.group(1) if match else None


def run(api: str) -> int:
    """Run every check and return the exit code."""
    report = Report()
    print(f"Cookbook check against {api}\n")

    # This repo.
    tests = unittest.defaultTestLoader.discover(str(REPO / "tests"))
    outcome = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(tests)
    report.check(outcome.wasSuccessful(), "unit tests", f"{len(outcome.failures) + len(outcome.errors)} failed "
                 f"(run: python3 -m unittest discover -s tests)", f"{outcome.testsRun} passed")
    links = broken_links(REPO)
    report.check(not links, "links and headings in the docs", "; ".join(links[:5]) + (" …" if len(links) > 5 else ""))
    skills = different_skill_files(REPO)
    report.check(not skills, ".claude/skills and .agents/skills are identical", "differ: " + ", ".join(skills))

    # Which pdp-near-completer-finder version the docs were last checked against.
    commit = checked_commit(REPO)
    gia_repo = Path(os.environ.get("GIA_REPO") or REPO.parent / "pdp-near-completer-finder")
    head = subprocess.run(["git", "-C", str(gia_repo), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip() if gia_repo.is_dir() else ""
    if commit and head and not head.startswith(commit) and not commit.startswith(head):
        report.line("INFO", "pdp-near-completer-finder has moved on",
                    f"README says {commit}, local checkout is {head}: review what changed, then update the README")
    elif commit:
        report.line("INFO", "README last checked against pdp-near-completer-finder", commit)

    # What the docs say about the dashboard.
    try:
        status, body = get(api, "/dashboard?institution=cmc")
    except OSError as error:
        report.line("FAIL", "dashboard API reachable", f"{error}. Use --api for a local copy")
        return 1
    if status != 200 or body is None:
        report.line("FAIL", "dashboard API reachable", f"answered {status}")
        return 1
    report.check(body.get("credit_threshold") == ALL_STOP_OUTS, "default credit filter is All stop-outs",
                 f'the API now defaults to {body.get("credit_threshold")!r}: update C10, C11, Play 3 and the scripts')
    rejected = [str(choice) for choice in (ALL_STOP_OUTS, *THRESHOLDS)
                if get(api, f"/dashboard?institution=cmc&credit_threshold={choice}")[0] != 200]
    report.check(not rejected, "every documented credit choice is accepted", "refused: " + ", ".join(rejected))
    report.check(get(api, "/dashboard?institution=cmc&credit_threshold=7")[0] == 422,
                 "an undocumented credit choice (7) is refused", "7 was accepted: the API's choices changed")
    labels = term_label_problems(body.get("terms", []) + [{"value": body.get("current_term", ""),
                                                           "label": body.get("current_term_label", "")}])
    report.check(not labels, "term labels match C9 (calendar year)", "; ".join(labels[:3]))
    # The API ignores parameters it doesn't know, so check the response carries them back.
    status, filtered = get(api, "/dashboard?institution=cmc&pathway_credits=9&student_term=all")
    missing = [key for key in ("pathway_credits", "student_terms") if not filtered or key not in filtered]
    report.check(status == 200 and not missing, "documented filters pathway_credits and student_term exist",
                 f"status {status}, missing from the response: {', '.join(missing)}: update Play 3")

    # The numbers, when the API shows the sample data that this machine also has.
    data_dir = default_data_dir()
    for college in ("cmc", "college_two"):
        status, college_body = get(api, f"/dashboard?institution={college}")
        if college_body and college_body.get("using_upload"):
            report.line("SKIP", f"{college} numbers", "the API is using an upload, which this machine can't see")
            continue
        if not data_dir.is_dir():
            report.line("SKIP", f"{college} numbers", f"no local data at {data_dir}: set GIA_REPO")
            continue
        for choice in (ALL_STOP_OUTS, 9):
            try:
                found = compare(college, choice, api)
            except (DataProblem, OSError, ValueError) as error:
                report.line("FAIL", f"{college} numbers at {choice}", str(error))
                continue
            report.check(not found, f"{college} numbers at {choice} match dashboard_counts.py",
                         f"{len(found)} differ, first: {found[0].strip() if found else ''}")

    print(f"\n{'All checks passed.' if not report.failed else f'{report.failed} check(s) failed.'}")
    return 1 if report.failed else 0


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="check_cookbook.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--api", default=DEFAULT_API, help=f"dashboard API base (default {DEFAULT_API})")
    return run(parser.parse_args(argv).api.rstrip("/"))


if __name__ == "__main__":
    sys.exit(main())
