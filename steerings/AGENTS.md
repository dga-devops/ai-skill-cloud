# AGENTS.md

Instructions for any AI agent working in this repository.

## Memory protocol (all agents)
Knowledge lives in the user's Obsidian vault (shared across all their projects). You author
entries there directly and update its indexes inline — no drag, no script.

### Resolve the vault path — per machine, NEVER hardcode
Use the first that exists: (1) `.memory-vault` at the repo root, (2) `~/.memory-vault`
(machine-wide default). If neither → INIT: ask the user for the full path to their vault's
Knowledge folder, then save it to `~/.memory-vault`. Never write memory until the path is confirmed.

### Init the vault if empty
If the folder lacks the structure (no `index.md` / `insights/` / `errors/`), scaffold it from
`vault-template.md` in this repo, and copy both `vault-template.md` and `knowledge-vault.md`
into `<vault>/_system/`.

### Mechanics
- The vault is OUTSIDE the workspace → use the shell for all reads/writes
  (Get-Content / Set-Content / Add-Content). ALWAYS UTF-8 (`-Encoding UTF8`; entries contain ❌). Quote paths.
- Pick the entry type that fits (one task may produce several):
  - reusable lesson → `insights/{slug}.md` (atomic, 3-5 lines)
  - general bug/incident → `errors/{slug}.md` + row in `errors/index.md`
  - project bug → `projects/{repo}/logs/errors/{YYYYMMDD-slug}.md`
  - decision with tradeoffs → `projects/{repo}/logs/decisions/{YYYYMMDD-slug}.md`
  - notable build/change → `projects/{repo}/logs/iterations/{slug}.md`
  - deep domain knowledge → `projects/{repo}/domain/{topic}/{slug}.md`
  - end of project session → update `projects/{repo}/hot.md`
- An error fix with a universal lesson → write the error doc AND a one-line `insights/` entry.
- Cross-project → root `insights/`/`errors/`; project-specific → under `projects/{repo}/`.
- English; lowercase-kebab slug (≤50 chars); date prefix `YYYYMMDD-` only for logs, never insights/domain;
  unique slug; link paths instead of pasting. All formats are in `vault-template.md`.
- Update the index inline: general error → append a row to `<vault>/errors/index.md`
  (`Add-Content -Encoding UTF8`); insight → insert a row in Recent Insights in `<vault>/index.md`
  (read → insert → write, preserving other sections); new domain page → add a row to `projects/{repo}/_index.md`.

## Shell & file access (Windows machines)
Goal: pick the right method on the first try. Never trial-and-error shell commands (the main credit drain).

### Files inside the workspace → use built-in file tools
Reading, searching, listing, and editing files inside the workspace should go through the
tool's native file capabilities, not the shell. This works regardless of shell.

### Files outside the workspace → use the shell
Built-in file tools are usually restricted to the workspace and will be denied outside it.
Go straight to the shell; do not waste a step trying a tool first.

### Pick commands per the machine's shell (PowerShell / cmd / WSL)
Assume PowerShell first. If a command fails on syntax, switch to the correct column once — do not keep guessing.

| Task | PowerShell | cmd | WSL / bash |
| --- | --- | --- | --- |
| Read whole file | `Get-Content -Path '<path>'` | `type "<path>"` | `cat '<path>'` |
| First N lines | `Get-Content '<path>' -TotalCount 50` | — | `head -n 50 '<path>'` |
| Last N lines | `Get-Content '<path>' -Tail 50` | — | `tail -n 50 '<path>'` |
| Search in file | `Select-String -Path '<path>' -Pattern 'term'` | `findstr "term" "<path>"` | `grep 'term' '<path>'` |
| List folder | `Get-ChildItem '<path>'` | `dir "<path>"` | `ls -la '<path>'` |
| Command separator | `;` | `&` | `&&` |
| D: drive path | `D:\dir\file` | `D:\dir\file` | `/mnt/d/dir/file` |

- Always quote paths containing spaces.
- Run bash from Windows via `wsl -d <distro> bash -c "<command>"` (e.g. `wsl -d Ubuntu-24.04 bash -c "cat '/mnt/d/...'"`).
- Large files: don't dump everything; limit lines (`-TotalCount`/`head`) or search directly (`Select-String`/`grep`/`findstr`).
- Thai / non-ASCII on Windows PowerShell 5.1: add `-Encoding UTF8` (e.g. `Get-Content '<path>' -Encoding UTF8`). WSL/bash is UTF-8 already.
- Writing outside the workspace: PowerShell `Set-Content -Path '<path>' -Value '<text>' -Encoding UTF8`; bash `printf '%s' '<text>' > '<path>'`. If it risks overwriting, ask the user first.
