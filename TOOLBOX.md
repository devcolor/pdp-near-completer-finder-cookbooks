# Toolbox: every skill, script, command and page

This page is a catalog of every tool for working with the stop-out dashboard. For each one it says
what it's for, who it's for, how to start it, and whether it can change anything.

You can also ask an AI assistant: in Claude Code, type `/toolbox` or ask "what can I use to …?".

**Who** column:
- **Anyone**: no technical setup needed.
- **Technical**: needs a terminal, the repos, or an AI coding tool.

**Changes things?** column:
- **No**: read-only. Safe to try.
- **Yes**: it changes data. Read the notes before using it.

The sample data that ships with the dashboard is made up. Nothing built on it is a finding about
real students or either college.

## Documents in this repo

| Document | What it's for | Who |
| --- | --- | --- |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Start here if you aren't an engineer: what everything is, plain-language words, and how to use the AI skills | Anyone |
| [PLAYBOOK.md](PLAYBOOK.md) | Which "play" to run for your role, from running the dashboard to adding data | Technical |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | Bugs and caveats in plain language, each with what you'll notice and what to do | Anyone |
| [RUNBOOK_UPLOADS.md](RUNBOOK_UPLOADS.md) | Step by step: changing the dashboard's data by uploading CSV files in the browser | Anyone |
| [TOOLBOX.md](TOOLBOX.md) | This page | Anyone |
| [DEPLOY.md](DEPLOY.md) | Running the dashboard on any platform: the minimum files, settings and checks | Technical |

## Skills in this repo

A skill is a set of instructions an AI assistant follows for one kind of request.
- **Claude Code:** type `/<name>`, or just ask the question and it picks the skill.
- **Other AI tools:** point the tool at `.agents/skills/<name>/SKILL.md`.

| Skill | Ask it things like | What it does | Who | Changes things? |
| --- | --- | --- | --- | --- |
| `toolbox` | "What tools do I have?", "How do I check my upload?" | Lists the skills, scripts and commands actually present, and explains them from this page | Anyone with Claude Code | No |
| `explain-dashboard` | "Why is Fall missing?", "What does 'near completer' mean here?", "Why did stop-outs jump?" | Explains a dashboard number, term or tile in plain language, and names the known issues that apply | Anyone with Claude Code | No |
| `data-health-check` | "Is my upload OK?", "Does the dashboard match the data?" | Runs the scripts below and explains the result: which data is in use, how stop-outs are counted, any problems found | Technical | No |

`data-health-check` uses the scripts below. If those scripts are removed, remove this skill too.

## Scripts in this repo

These may be removed after end-user feedback. If one is removed, delete its row here.

Both are Python 3.10 or newer, with nothing to install, and both also work as functions in a
notebook ([Play 6](PLAYBOOK.md#play-6-check-the-numbers-with-sql)). On Windows, type `py` instead of
`python3`.

| Script | What it does | Who | Changes things? | Start it with |
| --- | --- | --- | --- | --- |
| [`scripts/dashboard_counts.py`](scripts/dashboard_counts.py) | Works out the dashboard's executive numbers from the CSV files, the same way the app does. It reads uploaded files if there are any. It stops with a plain message on data problems that would break the dashboard | Technical | No | `python3 scripts/dashboard_counts.py cmc 9` |
| [`scripts/verify_against_api.py`](scripts/verify_against_api.py) | Compares those numbers with a running dashboard and lists any differences | Technical | No | `python3 scripts/verify_against_api.py cmc 9` |
| [`sql/dashboard_counts.sql`](sql/dashboard_counts.sql) | The query behind `dashboard_counts.py`, for porting to a college's own database | Technical | No | Run through `dashboard_counts.py` |
| [`scripts/check_cookbook.py`](scripts/check_cookbook.py) | One free, read-only check that the cookbook still matches the dashboard: tests, links, skill copies, documented behavior, and the numbers. Run it before sharing the cookbook and after gia-datathon changes | Technical | No | `python3 scripts/check_cookbook.py` |
| [`tests/test_dashboard_counts.py`](tests/test_dashboard_counts.py) | Checks `dashboard_counts.py` against hand-worked answers on tiny made-up files. `tests/test_check_cookbook.py` checks the cookbook check itself | Technical | No | `python3 -m unittest discover -s tests` |

Details and options: [Playbook, Play 6](PLAYBOOK.md#play-6-check-the-numbers-with-sql).

## Dashboard pages

| Page | Address on a local copy | What it's for | Who | Changes things? |
| --- | --- | --- | --- | --- |
| Executive view | http://localhost:3000/dashboard | Stop-outs, near completers, and the term with the most stop-outs | Anyone | No |
| Student services, Academic, Financial | `/dashboard/student-services`, `/dashboard/academic`, `/dashboard/financial` | The same data, from each office's side | Anyone | No |
| Upload | `/dashboard/upload` | Replace a college's data. See [the upload runbook](RUNBOOK_UPLOADS.md) | Anyone | **Yes** |

A hosted copy, if your team deploys one (see `docs/deploy.md` in gia-datathon), is open to anyone with the link
([C15](KNOWN_ISSUES.md#c15-the-hosted-dashboard-is-open-to-anyone-with-the-link)), and uploads
there aren't tested ([N1](KNOWN_ISSUES.md#n1-uploading-on-the-hosted-dashboard)).

## Dashboard data service (API)

What the pages call behind the scenes. Useful for scripts and spreadsheets.
- Local copy: `http://localhost:8000/api/v1`
- Hosted copy, if you have one: `https://<your-api>/api/v1`

| Call | What it returns or does | Changes things? |
| --- | --- | --- |
| `GET /dashboard?institution=cmc&credit_threshold=9` | Every executive number and list, for the filters given ([Play 3](PLAYBOOK.md#play-3-see-who-is-close-to-finishing) lists them) | No |
| `GET /dashboard/major?institution=cmc&major=BIOLOGY` | One major's students and the courses holding them up | No |
| `GET /uploads/requirements?institution=cmc` | The columns each file needs, the years saved, and how stop-outs are counted | No |
| `POST /uploads?institution=cmc` with four files | Saves an upload | **Yes** |
| `DELETE /uploads?institution=cmc&year=2024-25` | Removes one uploaded year | **Yes** |
| `DELETE /uploads?institution=cmc` | Removes the whole upload and returns to the sample data | **Yes** |

The interactive list of every call is at `/docs` on the data service, for example
http://localhost:8000/docs.

## Skills and tools in the main repo (gia-datathon)

| Tool | What it's for | Who | Changes things? |
| --- | --- | --- | --- |
| `pdp-data` skill | What a column in the PDP mock data means, profiling those files, simple questions about them | Technical | No |
| `metadata-advisor` skill | Which measures and breakdowns to look at, and safe aggregate queries. It never sees student records | Technical | No |
| `pdp-sandbox` skill | Building a new chart page in the Playground from the PDP data model | Technical | **Yes** (writes code) |
| `shadcn` skill | Building the app's user interface components | Technical | **Yes** (writes code) |
| PDP MCP server (`mcp/`) | Lets an AI assistant read table and column definitions, never student data | Technical | No |

These skills are read from the main repo's `.claude/skills/` (Claude Code) and `.agents/skills/`
(other tools).

## Commands in the main repo

Run from `gia-datathon/playground/` unless noted.

| Command | What it does | Changes things? |
| --- | --- | --- |
| `mise run api:dev` | Starts the data service on http://localhost:8000 (applies database updates first) | Local database only |
| `mise run web:dev` | Starts the dashboard on http://localhost:3000 | No |
| `mise run api:test-sqlite` | Runs the data service's tests | No |
| `mise run db:reset` | Deletes the local Playground database and starts fresh | **Yes** |
| `make check` (from the repo root) | Runs every data and foundation check | No |
| `DASHBOARD_DATA_DIR=/abs/path APP_ENV=development .venv/bin/python -m uvicorn app.main:app --port 8000` (from `playground/server_application/`) | Starts the data service on a copy of the CSV files ([Play 8, Option B](PLAYBOOK.md#option-b-edit-a-copy-of-the-csvs-local-api-only)) | No |

`mise tasks` lists every command, with a one-line description.

## Keeping this page current

- **Adding or removing a skill:** edit both copies, `.claude/skills/<name>/SKILL.md` and
  `.agents/skills/<name>/SKILL.md` (they must stay identical), and its row above. The `toolbox`
  skill reads the folders, so it notices a missing skill even before this page is updated.
- **Adding or removing a script:** update its row, and any skill that uses it.
- **Before sharing the cookbook, and after gia-datathon changes:** run
  `python3 scripts/check_cookbook.py`. See [Keeping the cookbook current](README.md#keeping-the-cookbook-current).
