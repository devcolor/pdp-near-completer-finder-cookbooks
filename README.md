# pdp-near-completer-finder-cookbooks

Guides, AI skills and scripts for using, checking and deploying the GIA stop-out and near-completer
dashboard from the [pdp-near-completer-finder](https://github.com/devcolor/pdp-near-completer-finder) repo.

**Not an engineer? Start with [GETTING_STARTED.md](GETTING_STARTED.md).**

| Page | For | What it covers |
| --- | --- | --- |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Anyone | What everything is, plain-language words, and how to use the AI skills |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | Anyone | Bugs and caveats in plain language, each with what you'll notice and what to do |
| [RUNBOOK_UPLOADS.md](RUNBOOK_UPLOADS.md) | Anyone | Changing the dashboard's data by uploading CSV files, step by step |
| [TOOLBOX.md](TOOLBOX.md) | Anyone | Every skill, script, command and dashboard page, and whether it changes data |
| [PLAYBOOK.md](PLAYBOOK.md) | Technical | Which play to run for your role, from running the dashboard to adding data |
| [DEPLOY.md](DEPLOY.md) | Technical | Deploying on any platform: the minimum files from pdp-near-completer-finder, settings, checks |

AI skills: `toolbox`, `explain-dashboard`, `data-health-check`, in `.claude/skills/` (Claude Code) and
`.agents/skills/` (other tools). Scripts, in Python with nothing to install: `scripts/dashboard_counts.py`
and `scripts/verify_against_api.py`, with the SQL in `sql/` and tests in `tests/`.

## Keeping the cookbook current

Last checked on 2026-11-23 against the original datathon repo, before the move to
pdp-near-completer-finder. After the next check, record it here as: Last checked against
pdp-near-completer-finder commit `<commit>` (date).

The dashboard changes often, and the cookbook can fall behind. Before sharing it, and after
pdp-near-completer-finder changes, run:

```bash
python3 scripts/check_cookbook.py                                  # against a local copy (localhost:8000)
python3 scripts/check_cookbook.py --api https://<your-api>/api/v1   # or a hosted copy
```

It's free (it runs on your computer, with no GitHub Actions, no paid services and no AI), takes
about 10 seconds, and only reads. It checks:
- this repo: the tests, the links, and the two skill copies;
- that the dashboard still behaves the way the docs say: the default credit filter, the accepted
  credit choices, how terms are labeled, the filters the playbook lists;
- the numbers, against `dashboard_counts.py`.

Each line says PASS, FAIL, SKIP or INFO, and every FAIL names the page to update. When it passes
against a newer pdp-near-completer-finder, update the commit above.

The bundled data is synthetic until a college uploads its own. Nothing built on synthetic data is a
finding about real students or institutions.
