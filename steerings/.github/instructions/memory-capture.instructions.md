---
description: "Use after finishing a response when: a bug's root cause was non-obvious, a decision had real tradeoffs with a specific reason, a tool/environment gotcha would trip someone up again, or a reusable workflow was built this session. Skip for general concept explanations, standard comparisons, syntax lookups, or anything a fresh search would answer faster."
---

# Memory capture (write to the user's Obsidian vault)

Knowledge lives in the user's Obsidian vault (shared across all their projects). You author
entries there directly and update its indexes inline — no drag, no script.

## Resolve the vault path — per machine, NEVER hardcode
Use the first that exists:
1. `.memory-vault` at the repo root
2. `~/.memory-vault` (machine-wide default)

If neither exists → INIT: ask the user for the full path to their vault's Knowledge folder,
then save it to `~/.memory-vault` (so every project on this machine reuses it). Never write
memory until the path is known and confirmed.

## Init the vault if empty
If the folder lacks the structure (no `index.md` / `insights/` / `errors/`), scaffold it from
`vault-template.md` in this repo (folders + index.md + errors/index.md), and copy both
`vault-template.md` and `knowledge-vault.md` into `<vault>/_system/` as the vault's own reference.
Then proceed.

## Mechanics — the vault is OUTSIDE the workspace
- Use the shell for all vault reads/writes (Get-Content / Set-Content / Add-Content); file
  tools are blocked outside the workspace.
- ALWAYS write UTF-8 (PowerShell: `-Encoding UTF8`) — entries contain non-ASCII (e.g. ❌).
- Quote every path.

## What to write — pick the type(s) that fit (one task may produce several)
| You did | Write to | Format |
| --- | --- | --- |
| Distilled a reusable lesson | `insights/{slug}.md` | atomic, 3-5 lines (below) |
| Fixed a general bug/incident | `errors/{slug}.md` + row in `errors/index.md` | error (below) |
| Fixed a bug in a specific project | `projects/{repo}/logs/errors/{YYYYMMDD-slug}.md` | error (below) |
| Made a decision with tradeoffs | `projects/{repo}/logs/decisions/{YYYYMMDD-slug}.md` | see `vault-template.md` |
| Built/changed something notable | `projects/{repo}/logs/iterations/{slug}.md` | see `vault-template.md` |
| Documented deep domain knowledge | `projects/{repo}/domain/{topic}/{slug}.md` | free-form reference page |
| Ended a work session on a project | update `projects/{repo}/hot.md` | see `vault-template.md` (≤30 lines) |

- An error fix with a UNIVERSAL lesson → write the full error doc AND add a one-line `insights/` entry.
- Cross-project/general → root `insights/` & `errors/`. Project-specific → under `projects/{repo}/` (use the repo folder name).
- English only; lowercase-kebab slug (≤50 chars); unique slug (add a word if it exists); link paths, don't paste large content.
- Date prefix `YYYYMMDD-` ONLY for logs (errors/decisions inside `projects/*/logs/`); NEVER for insights or domain pages.

Insight format (atomic — the distilled lesson, not the full story):
```
# {insight as a statement}

{2-4 sentences with evidence}

**Evidence**: {source}
**So what**: {action}

Tags: #topic
```

Error format (the full story — diagnosis, cause, fix):
```
# ❌ {what happened}

Date: YYYY-MM-DD
Category: logic | data | config | integration | os
Severity: 🔴 Critical | 🟡 Medium | 🟢 Low

## What
## Root Cause
## Fix
## Lesson
```

## Update the index inline (you author it → no merge problem)
- general error → append one row to `<vault>/errors/index.md` with `Add-Content -Encoding UTF8`
  (it is header + table, so appending lands correctly).
- insight → insert a row in the Recent Insights table in `<vault>/index.md` (read → insert → write, preserve other sections).
- new domain page → add a row to `<vault>/projects/{repo}/_index.md`.
- decisions / iterations / project-specific errors → no central index to update.
