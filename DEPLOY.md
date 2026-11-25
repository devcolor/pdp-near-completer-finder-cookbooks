# Deploying the stop-out dashboard on any platform

How to run the dashboard from the `pdp-near-completer-finder` repo on a platform other than Vercel: a college's own
servers, a container platform, or a single virtual machine. It lists the minimum files to copy, the
settings to give, and how to check the result.

**In plain terms:** the dashboard is two programs and a folder of CSV files.

| Piece | What it is | Where it runs |
| --- | --- | --- |
| **Data service** (API) | A Python program that reads the CSV files and works out every number | A server that can run Python |
| **Website** | The pages people click through. It asks the data service for the numbers | A server that can run Node.js, or a static web host (see [Step 3](#step-3-build-and-serve-the-website)) |
| **Data files** | The four CSV files per college, plus a list of majors | A folder the data service can read |

Everything in this guide was tested on 2026-11-11, using a copy that held **only** the files listed
below. The test ran in production mode, on a Mac, without Vercel. The results are under
[What was tested](#what-was-tested).

> The dashboard has **no sign-in of its own**. Whoever can reach its address can see it and upload to
> it ([C15](KNOWN_ISSUES.md#c15-the-hosted-dashboard-is-open-to-anyone-with-the-link)). Put it behind
> your organization's login (single sign-on, VPN, or an internal-only network) before loading real
> student data.

## The minimum files

Paths are inside the `pdp-near-completer-finder` repo. Keep the folder layout the same: the data service finds the
data model, and by default the data files, by relative path.

### Data service

| Path | Needed for | Size |
| --- | --- | --- |
| `playground/server_application/app/` | The program itself | ~450 KB |
| `playground/server_application/pyproject.toml` | The list of Python packages | |
| `playground/server_application/uv.lock` | The exact package versions | |
| `playground/server_application/.python-version` | Python version (3.14) | |
| `normalized-data-model/`, **without** its `data/`, `output/`, `logs/` and `tests/` folders | **Installing only.** It is listed as a package the data service depends on, so installing fails without it (`Distribution not found`). The dashboard never runs its code | ~550 KB |
| `playground/server_application/.env.production` | *Optional.* Production defaults. If you copy it, override `CORS_ORIGINS` and `DASHBOARD_UPLOAD_DIR` (see [Settings](#settings)) | |

### Data files

The default location is `gia-pre-implementation/synthetic-datasets/`. Put them anywhere and point
`DASHBOARD_DATA_DIR` at the folder.

| Path inside the data folder | What it is |
| --- | --- |
| `pathway_map.csv` | Which pathway each major belongs to. Used by the major view and the pathway charts |
| `cmc/csv/students.csv`, `college_two/csv/students.csv` | One row per student per academic year |
| `cmc/csv/student_institutional_profile.csv`, and the same for `college_two` | Holds, parenting, work, housing |
| `cmc/csv/course_schedule.csv`, and the same for `college_two` | When and where courses are offered |
| `cmc/csv/course_detail.csv`, and the same for `college_two` | Every course every student took |

That is 9 files, about 9.4 MB. Other files in that folder (`program_credits.csv`, `validation.json`,
`pathway_program_map.csv`, the rebuild scripts) are not read by the dashboard.

These files also set the rules for uploads. The Upload page requires every column these files
have, so keep them even after a college uploads its own data.

### Website

| Path | Needed for |
| --- | --- |
| `playground/client_application/package.json` | The list of packages and the build commands |
| `playground/client_application/bun.lock` | The exact package versions |
| `playground/client_application/next.config.ts` | Build settings |
| `playground/client_application/tsconfig.json`, `next-env.d.ts` | TypeScript settings |
| `playground/client_application/src/` | The pages |
| `playground/client_application/public/` | Images and icons |

### Not needed

Everything else in the repo: `data/raw/`, `measures/`, `gap_finder/`, `mcp/`, `notebooks/`, `docs/`,
the raw course catalogs, `playground/server_application/alembic/` (database migrations; the
dashboard needs no tables), tests, Storybook files, and any `node_modules/`, `.venv/` or `.next/`
folders, which are rebuilt.

## Tools

| Tool | Version tested | Used for |
| --- | --- | --- |
| Python | 3.14 | Running the data service |
| uv | 0.13.7 | Installing the data service's packages |
| Node.js | 24 | Building and running the website |
| bun | 1.4.3 | Installing the website's packages and building it |

These match `playground/mise.toml`. With [mise](https://mise.jdx.dev) installed, `mise install` in
`playground/` gets all four.

## Settings

### Data service (environment variables, read when it starts)

| Setting | Required? | Value | Notes |
| --- | --- | --- | --- |
| `APP_ENV` | Yes | `production` | Turns off the `/docs` page. Also loads `.env.production` if that file is present |
| `DATABASE_URL` | **Yes** | For example `sqlite:////srv/dashboard/health.db`, or a PostgreSQL address | The service **won't start without it**. The dashboard keeps nothing in the database. Only `/health` uses it, to report that it can connect. A SQLite file works, with no tables needed |
| `CORS_ORIGINS` | Yes | The website's address, as a JSON list: `["https://dashboard.example.edu"]` | Without the website's exact address here, browsers block the website from reading the numbers. `.env.production` sets a placeholder (`https://example.com`), so override it |
| `DASHBOARD_DATA_DIR` | If the data isn't at the default path | Absolute path to the data folder | Relative paths start at `playground/server_application/` |
| `DASHBOARD_UPLOAD_DIR` | If uploads are allowed | Absolute path to a **writable, lasting** folder | Default: `uploads/` inside the data folder. See [Uploads need lasting storage](#uploads-need-lasting-storage) |
| `SANDBOX_ENABLED` | No | `false` | Example-chart endpoints. Off in production |

### Website (set when building, not when running)

| Setting | Required? | Value | Notes |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | **Yes** | The data service's address plus `/api/v1`: `https://dashboard-api.example.edu/api/v1` | Built into the pages. **If missing, the website calls `https://api.example.com/api/v1`, a placeholder, and shows no data.** Change the address only by rebuilding |
| `NEXT_PUBLIC_APP_ENV` | Recommended | `production` | |

## Step 1: Copy the files

Copy the paths above into one folder on the server, keeping their layout:

```
deploy/
├── normalized-data-model/            (without data/, output/, logs/, tests/)
├── playground/
│   ├── server_application/           (app/, pyproject.toml, uv.lock, .python-version)
│   └── client_application/           (package.json, bun.lock, next.config.ts, tsconfig.json,
│                                      next-env.d.ts, src/, public/)
└── (data folder anywhere, for example /srv/dashboard/data with pathway_map.csv, cmc/, college_two/)
```

## Step 2: Install and start the data service

```bash
cd deploy/playground/server_application
uv sync --frozen --no-dev

APP_ENV=production \
DATABASE_URL="sqlite:////srv/dashboard/health.db" \
DASHBOARD_DATA_DIR=/srv/dashboard/data \
DASHBOARD_UPLOAD_DIR=/srv/dashboard/uploads \
CORS_ORIGINS='["https://dashboard.example.edu"]' \
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On a container platform, the same two commands go in the image: `uv sync` when building, `uvicorn`
when starting. No Dockerfile ships with the repo, and none was tested.

## Step 3: Build and serve the website

```bash
cd deploy/playground/client_application
bun install --frozen-lockfile
NEXT_PUBLIC_APP_ENV=production \
NEXT_PUBLIC_API_BASE_URL=https://dashboard-api.example.edu/api/v1 \
bun run build
bun run start -- -p 3000
```

`bun run start` needs Node.js on the server. The build reported every page as static, so a static
web host might serve the built files instead, but that wasn't tested. Use `bun run start` unless you
test the static route yourself.

## Step 4: Check it worked

| Check | Expected |
| --- | --- |
| `curl https://<api>/api/v1/health` | `{"status":"ok","environment":"production", … "database":{… "status":"connected" …}}` |
| `curl -o /dev/null -w '%{http_code}' https://<api>/docs` | `404`: the docs page is off in production |
| `curl -s -D - -o /dev/null -H 'Origin: https://<website>' 'https://<api>/api/v1/dashboard?institution=cmc' \| grep -i access-control-allow-origin` | Your website's address. If nothing comes back, fix `CORS_ORIGINS` |
| Open `https://<website>/dashboard` | The executive view with numbers |
| From this cookbook repo: `python3 scripts/verify_against_api.py cmc 6 --api https://<api>/api/v1 --data-dir <data folder>` | `All match.` Run it on a machine that can read the same data folder. Add `--upload-dir` if uploads are in use |

## Decisions for your platform

### Uploads need lasting storage

An upload is saved as files in `DASHBOARD_UPLOAD_DIR`. For uploads to work properly:

- **The folder must be writable.** Vercel's app folder is read-only, which is why the Vercel setup
  saves uploads to `/tmp/dashboard-uploads`.
- **It must survive restarts.** `/tmp` on Vercel is cleared when a new copy of the service starts, so
  uploads there disappear
  ([N1](KNOWN_ISSUES.md#n1-uploading-on-the-hosted-dashboard)).
- **Every copy of the service must see the same folder.** If the platform runs several copies at
  once, use a shared disk, or run exactly one copy. Otherwise an upload lands on one copy and the
  others never see it.

If none of that is possible, don't offer uploads. Replace the data files and restart instead.

### Restart after replacing the data files

The service re-reads a CSV file when it changes. But the course drop and fail rates are read **once**
and kept until the service restarts, and they always come from the base data files, never from
uploads ([B4](KNOWN_ISSUES.md#b4-course-drop-and-fail-rates-ignore-uploads)). After replacing the
base files, restart the service.

### Changing the data service's address means rebuilding the website

`NEXT_PUBLIC_API_BASE_URL` is fixed when the website is built. If the data service moves, rebuild and
redeploy the website.

### Real student data

The synthetic files are made up. For real data, follow your college's rules on where student
records may be stored. The upload folder will hold those records, and so will the data folder if
you replace the base files.

## How a Vercel setup maps to this

For reference if you deploy to Vercel (step by step: `docs/deploy.md` in pdp-near-completer-finder). Two Vercel projects deploy from the repo:

| Vercel project | Folder | Build | Settings |
| --- | --- | --- | --- |
| `<your-api-project>` | `playground/server_application` | `vercel.json` copies the data files into the app folder (`cp -R ../../gia-pre-implementation/synthetic-datasets synthetic-datasets`). `.vercelignore` at the repo root leaves out what isn't needed | `APP_ENV`, `DATABASE_URL`, `CORS_ORIGINS`, `DASHBOARD_DATA_DIR`, and `DASHBOARD_UPLOAD_DIR` from `.env.production` |
| `<your-web-project>` | `playground/client_application` | Next.js default | `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV` |

The values are stored in Vercel and weren't read for this guide.

## What was tested

On 2026-11-11, from a folder holding only the files above (data service about 450 KB, data model
about 550 KB, data 9.4 MB):

- **Installing:**
  - `uv sync --frozen --no-dev` succeeded.
  - It failed without `normalized-data-model/`.
- **Starting:**
  - Production mode with a fresh, empty SQLite file: `/health` answered `ok` with the database
    connected.
  - `/docs` answered 404.
  - Without `DATABASE_URL`, the service refused to start.
- **CORS:** the dashboard answered with the configured website address for that origin, and with
  no CORS header for any other origin.
- **Numbers:** `verify_against_api.py` matched for CMC and College 2.
- **Uploads:**
  - With `DASHBOARD_UPLOAD_DIR` set to a separate folder, an upload saved there and the dashboard
    used it.
  - `verify_against_api.py --upload-dir` matched the uploaded two-year set.
  - `DELETE` restored the sample data.
- **Website:**
  - `bun install --frozen-lockfile` and `bun run build` succeeded from only the files listed.
  - The built pages contained the configured data service address, and not the placeholder.
  - `bun run start` served `/dashboard` and `/dashboard/upload` with status 200.

**Not tested:**
- A real browser click-through. The checks used `curl`.
- PostgreSQL as the database.
- A container image.
- Serving the website as static files.
- Windows.
- Running more than one copy of the data service.
