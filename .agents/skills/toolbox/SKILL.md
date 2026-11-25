---
name: toolbox
description: List and explain the skills, scripts, commands, documents and dashboard pages available for the GIA stop-out dashboard, in plain language. Use when someone asks what tools they have, which tool to use for a task ("how do I check my upload?", "is there a command for X?"), or what a specific script, skill or command does.
---

# toolbox

Answer "what can I use, and how?" for the stop-out dashboard. The reader may be a subject-matter
expert (advisor, dean, institutional researcher), not an engineer. Write for them.

## Steps

1. **See what is actually present.** Don't trust memory or the catalog alone. Scripts may have been
   removed. From the root of this repo (gia-datathon-cookbooks):

   ```bash
   ls .agents/skills .claude/skills scripts sql *.md
   ```

   If the main repo is next to this one (`../gia-datathon`, or `$GIA_REPO`), also list
   `../gia-datathon/.agents/skills`.

2. **Read `TOOLBOX.md`** for the explanation of each item: what it's for, who it's for, how to start
   it, and whether it changes anything.

3. **Answer the question.**
   - **"What do I have?"** Group the answer as TOOLBOX.md does: documents, skills, scripts,
     dashboard pages, data service calls, main-repo tools. Give one plain sentence each.
   - **"Which one for X?"** Recommend one tool. Say why in one sentence, give the exact command or
     page, and say whether it changes data.
   - **"What does X do?"** Explain it from TOOLBOX.md, and from the tool's own file if needed
     (`SKILL.md`, or the comment at the top of the script).

4. **Report gaps honestly.**
   - **Listed in TOOLBOX.md but missing from disk:** say it was removed, and that TOOLBOX.md needs
     its row deleted.
   - **On disk but not listed:** say it isn't documented yet, and describe it from its own file.

## Rules

- Mark anything that changes data (uploads, deletes, `db:reset`) clearly. Before suggesting it, say
  what it changes and how to undo it.
- Point non-technical readers to the documents and dashboard pages first, and to scripts only
  through a technical teammate.
- Don't run scripts or commands in this skill. It only explains. For checks, suggest the
  `data-health-check` skill.
- Say the data is synthetic when the question concerns the bundled sample data.
