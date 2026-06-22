---
applyTo: '**'
description: "Shell and file access rules for Windows machines. Use whenever running terminal commands, reading or writing files, or working with paths — especially files outside the workspace. Covers PowerShell, cmd, and WSL bash syntax."
---

# Shell & file access (Windows machines)
Goal: pick the right method on the first try. Never trial-and-error shell commands (the main credit drain).

## Files inside the workspace → use built-in file tools
Reading, searching, listing, and editing files inside the workspace should go through the
tool's native file capabilities, not the shell. This works regardless of shell.

## Files outside the workspace → use the shell
Built-in file tools are usually restricted to the workspace and will be denied outside it.
Go straight to the shell; do not waste a step trying a tool first.

## Pick commands per the machine's shell (PowerShell / cmd / WSL)
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
