"""Tests for the offline parts of scripts/check_cookbook.py: term labels, links, skill copies.

Run from the repo root: python -m unittest discover -s tests
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_cookbook import broken_links, different_skill_files, term_label_problems  # noqa: E402


class TermLabelTest(unittest.TestCase):
    """C9: terms are labeled "<2-digit calendar year> <season>"."""

    def test_calendar_year_labels_pass(self):
        """The current labels."""
        self.assertEqual(term_label_problems([
            {"value": "Fall 2024", "label": "24 Fall"},
            {"value": "Spring 2025", "label": "25 Spring"},
        ]), [])

    def test_old_winter_labels_fail(self):
        """The labels the dashboard used before 2026-11-11."""
        problems = term_label_problems([{"value": "Fall 2024", "label": "24-25 Winter"}])
        self.assertEqual(len(problems), 1)
        self.assertIn("24-25 Winter", problems[0])

    def test_unknown_shapes_are_ignored(self):
        """Terms the docs don't describe can't contradict them."""
        self.assertEqual(term_label_problems([{"value": "Intersession", "label": "Intersession"}]), [])


class RepoChecksTest(unittest.TestCase):
    """broken_links and different_skill_files on a tiny made-up repo."""

    def setUp(self):
        """A fresh folder per test."""
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        """Remove it."""
        self._tmp.cleanup()

    def test_links(self):
        """Good links pass; a missing file and a missing heading are reported; code spans are skipped."""
        (self.root / "A.md").write_text("# Title\n\n## Second part\n")
        (self.root / "B.md").write_text(
            "[ok](A.md#second-part) [self](#here) [web](https://example.com)\n# Here\n"
            "`[skipped](Nope.md)` [gone](Nope.md) [bad](A.md#third-part)\n"
        )
        problems = broken_links(self.root)
        self.assertEqual(len(problems), 2)
        self.assertTrue(any("Nope.md" in problem for problem in problems))
        self.assertTrue(any("third-part" in problem for problem in problems))

    def test_skill_copies(self):
        """Identical copies pass; a changed or one-sided file is named."""
        for side in (".claude", ".agents"):
            (self.root / side / "skills" / "one").mkdir(parents=True)
            (self.root / side / "skills" / "one" / "SKILL.md").write_text("same")
        self.assertEqual(different_skill_files(self.root), [])
        (self.root / ".agents" / "skills" / "one" / "SKILL.md").write_text("changed")
        (self.root / ".claude" / "skills" / "one" / "extra.md").write_text("only here")
        self.assertEqual(sorted(different_skill_files(self.root)), ["one/SKILL.md", "one/extra.md"])


if __name__ == "__main__":
    unittest.main()
