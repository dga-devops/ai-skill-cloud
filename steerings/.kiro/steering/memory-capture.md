---
inclusion: always
---

# Memory capture (write to the user's Obsidian vault)

## MANDATORY ACTION — do this at the END of a response when the bar is met
After finishing, ask: "Would this save real time if encountered again?"
- YES → write a memory entry to the vault before ending your response. Do not wait to be asked.
- NO → skip.

**Write only if at least one is true:**
- A bug whose root cause was non-obvious (not fixable by reading the error message alone)
- A decision with real tradeoffs (chose X over Y for a specific reason that isn't common knowledge)
- A gotcha specific to this environment/tool/version that would trip someone up again
- A reusable pattern or workflow built during this session (not a general concept anyone can Google)

**Never write for:**
- Explanations of general concepts (what JWT is, how promises work)
- Standard comparisons available in any docs/article
- One-liner lookups, syntax questions, typo fixes
- Anything a fresh search would answer faster than reading the vault entry

## Resolve the vault path — per machine, NEVER hardcode

`.memory-vault` is a **pointer FILE**, not the vault itself. It is a one-line text file whose
content is the absolute path to the real vault (the Obsidian Knowledge folder), e.g.:

```
D:\Obsidian Vault\Knowledge
```

To find the vault, look for this pointer file in order and use the first that exists:
1. `.memory-vault` (file) at the repo root
2. `~/.memory-vault` (file) — machine-wide default

Then **read the file's content** to get `<vault>` = the real vault path. Always write memory
INTO `<vault>` (the path read from the file). NEVER create folders or write entries inside the
pointer file's own location (e.g. do not create `~/.memory-vault/insights/`). The pointer file
stays a plain file; only its text content matters.

Common mistake to avoid: treating `~/.memory-vault` as if it were the vault directory. It is
not — it only holds the path string. If you see it is a file, that is correct; open it and read
the path.

If neither pointer file exists → INIT: ask the user for the absolute path to their vault's
Knowledge folder, then write that path as the single line of `~/.memory-vault` (so every project
on this machine reuses it). Never write memory until `<vault>` is known and confirmed.

Sanity check before writing: confirm `<vault>` (the path read from the pointer) exists and is a
directory. If the pointer file is missing its path content (empty), treat it as INIT and ask.

## Init the vault if empty
After resolving `<vault>` from the pointer, if `<vault>` lacks the structure
(no `index.md` / `insights/` / `errors/`), scaffold it INSIDE `<vault>` from `vault-template.md`
in this repo (folders + index.md + errors/index.md), and copy both `vault-template.md` and
`knowledge-vault.md` into `<vault>/_system/` as the vault's own reference. Then proceed.
(If `<vault>` already has the structure, do not re-scaffold — just write entries.)

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

Insight format (atomic — the distilled lesson, not the full story) and Error format
(the full story — what / root cause / self-check / fix / lesson) are defined in
`vault-template.md` (the single source of truth). Follow the templates there; do NOT
duplicate them here. After init, the same file is also available at `<vault>/_system/vault-template.md`.

## Update the index inline (you author it → no merge problem)
- general error → append one row to `<vault>/errors/index.md` with `Add-Content -Encoding UTF8`
  (it is header + table, so appending lands correctly).
- insight → insert a row in the Recent Insights table in `<vault>/index.md` (read → insert → write, preserve other sections).
- new domain page → add a row to `<vault>/projects/{repo}/_index.md`.
- decisions / iterations / project-specific errors → no central index to update.
