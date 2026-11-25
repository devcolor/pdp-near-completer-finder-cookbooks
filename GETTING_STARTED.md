# Getting started (for people who aren't engineers)

Start here if you know students, programs and advising well, and want to use the stop-out dashboard
or its AI helpers, but you don't write software.

> The sample data that comes with the dashboard is made up. Nothing in it is a finding about real
> students or either college.

## What this is, in one minute

- **The dashboard** shows students who stopped attending while still owing credits on their major
  ("stop-outs"), and students close to finishing ("near completers"). There is one view for
  executives, and one each for student services, academic affairs and financial aid.
- **This repo** (a shared folder of files, kept on GitHub) holds the instructions for using the
  dashboard, the list of known problems, and a few AI helpers called **skills**.

## Read these, in this order

| Order | Page | Why |
| --- | --- | --- |
| 1 | This page | What everything is, and how to start |
| 2 | [Known issues](KNOWN_ISSUES.md) | What can surprise you, in plain language: bugs (B), caveats (C), things not tested yet (N) |
| 3 | [Upload runbook](RUNBOOK_UPLOADS.md) | Only if you will change the dashboard's data |
| 4 | [Toolbox](TOOLBOX.md) | Every tool, marked "Anyone" or "Technical" |

The [Playbook](PLAYBOOK.md) and the [Deploy guide](DEPLOY.md) are written for technical teammates.
You can skip them, or ask an AI skill to explain a part.

## Words you'll see

| Word | Means |
| --- | --- |
| **Stop-out** | A student who left before the term now in progress, still owing credits on their major |
| **Near completer** | A student within a set number of credits of finishing their major, whether still enrolled or not. With the default "All stop-outs" filter, the dashboard's near-completer count is simply every stop-out |
| **Credit filter** | The choice at the top of the dashboard. It starts at "All stop-outs". Picking a number (3, 6, 9, 12, 15 or 24) narrows to students within that many credits of finishing, and that also includes students still enrolled ([B5](KNOWN_ISSUES.md#b5-a-stop-outs-within-n-credits-choice-also-lists-enrolled-students)). "Stop-outs who never started" (0) means students with no credits applied to their major yet |
| **Current term** | The newest term in the data. The dashboard treats it as still in progress |
| **Academic year (`pdp_year`)** | Written like `2024-25`. **Fall starts the year:** Fall 2024 and Spring 2025 are both `2024-25` |
| **CSV file** | A spreadsheet saved as plain text. Excel can open and save them (*Save As > CSV UTF-8*) |
| **Upload** | Replacing the dashboard's data with your own CSV files, on the Upload page |
| **Sample data** | The made-up data the dashboard ships with. Also called "synthetic" |
| **API** | The part of the dashboard that works out the numbers. The pages ask it for them |
| **Skill** | Instructions that teach an AI assistant one job, such as explaining the dashboard |
| **Claude Code** | The AI assistant that uses the skills in this repo |

## Using the AI skills

### What you need, once

1. **Access to Claude Code.** It runs in a desktop app, in a web browser (claude.ai/code), or in a
   terminal. Your team decides which, and who pays for it.
2. **This repo open in Claude Code.** A technical teammate can set this up with you once. The
   skills only appear when Claude Code is started inside this repo.
3. **For `data-health-check` only:** the main dashboard repo (`gia-datathon`) next to this one on
   the same computer. A technical teammate sets this up.

Skills only appear in a session started **after** they were added. If `/toolbox` isn't recognized,
start a new session.

### The three skills

| Skill | Good for | Who | Try asking |
| --- | --- | --- | --- |
| `toolbox` | Finding the right tool, document or page | Anyone | "What tools do I have?" or "How do I add a missing Fall term?" |
| `explain-dashboard` | Understanding a number, a word, or a surprising result | Anyone | "Why can't I find Fall 2024?", "Why are there two near-completer numbers?", "Can I share this count?" |
| `data-health-check` | Checking which data the dashboard is reading, and whether it's healthy | A technical teammate, or anyone once set up | "Is my upload OK?" |

To use one, type `/` and its name (for example `/explain-dashboard`), then your question. Or just ask
your question: Claude Code usually picks the right skill on its own.

### What the skills will and won't do

| They will | They won't |
| --- | --- |
| Explain in plain language and point to the matching known issue (for example "C9") | Show student names or IDs, or ask you for them |
| Say when an answer comes from sample data | Make up numbers. For current figures, read them off the dashboard or run `data-health-check` |
| Say plainly when the documents don't answer something | Upload, delete or change any data. Every skill here only reads |

`data-health-check` runs two small programs on your computer. Claude Code asks your permission
before running anything. It's safe to say yes: the programs only read files.

### If a skill gives a wrong or confusing answer

- Check the known issue it names. The [Known issues](KNOWN_ISSUES.md) page is the source it reads.
- Tell your team. The fix is usually a correction to that page, which every skill then picks up.

## Common first questions

| Question | Where the answer is |
| --- | --- |
| "Why do Fall and Spring show different years?" | Terms are labeled by calendar year: Fall 2024 is "24 Fall", Spring 2025 is "25 Spring", and both are academic year 2024-25 ([C9](KNOWN_ISSUES.md#c9-term-labels-use-the-calendar-year-not-the-academic-year)) |
| "Why did the numbers change after an upload?" | [C1](KNOWN_ISSUES.md#c1-the-first-upload-replaces-the-sample-data-instead-of-adding-to-it) and [C4](KNOWN_ISSUES.md#c4-adding-a-second-year-changes-how-stop-outs-are-counted) |
| "Can I upload real student data?" | Not on the hosted site: it is open to anyone with the link ([C15](KNOWN_ISSUES.md#c15-the-hosted-dashboard-is-open-to-anyone-with-the-link)). Ask your team about a protected copy |
| "Why does the list stop at 40 students?" | [C11](KNOWN_ISSUES.md#c11-the-student-list-shows-at-most-40-students) |
| "Who sets the dashboard up somewhere new?" | A technical teammate, with the [Deploy guide](DEPLOY.md) |
