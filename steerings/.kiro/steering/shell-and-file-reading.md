---
inclusion: always
---

# Shell & File Reading

Goal: pick the right method on the first try. Never trial-and-error shell commands (the main credit drain).

## 1. Files inside workspace → always use tools (shell-agnostic)
Works the same whether the machine is PowerShell, cmd, or WSL:

| Task | Tool |
| --- | --- |
| Read file | `read_file` / `read_files` |
| Search text in files | `grep_search` |
| Find file by name | `file_search` |
| List a folder | `list_directory` |

Tools only work for files inside the workspace or `~/.kiro`.

## 2. Files outside workspace → must use shell
- `read_file` / `grep_search` / `list_directory` are blocked: "Access denied: File access is restricted to workspace".
- Don't waste a step trying a tool first. Go straight to shell, picking commands per the machine's shell (section 3).

## 3. Detect which shell this machine uses
Three possibilities: **PowerShell**, **cmd**, **WSL (Ubuntu/bash)**.
- Assume **PowerShell** first (most common default on Windows).
- Signs of cmd: PowerShell cmdlets or `;` / `&&` fail.
- Signs of WSL/bash: paths look like `/mnt/d/...`, bash prompt, cmdlets unknown.
- If the first command fails on syntax, switch to the correct column **once**. Do not keep guessing.

## 4. Command table by shell
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
- To run bash from Windows, wrap it: `wsl -d <distro> bash -c "<command>"` (e.g. `wsl -d Ubuntu-24.04 bash -c "cat '/mnt/d/...'"`).

## 5. Large files = watch credit
Don't dump a whole file unless needed; all output enters context.
- Need structure/header → limit lines (`-TotalCount`, `head`).
- Looking for something specific → search directly (`Select-String`, `grep`, `findstr`) instead of reading all then scanning.
- Read the whole file only when it's small or you genuinely need all of it.

## 6. Encoding (Thai / UTF-8 files)
- Windows PowerShell 5.1 defaults to non-UTF-8; Thai files may be garbled.
- For non-ASCII files, specify encoding: `Get-Content '<path>' -Encoding UTF8`.
- WSL/bash is UTF-8 by default; nothing extra needed.

## 7. Writing files
- Inside workspace → use tools `fs_write` / `fs_append` / `str_replace`.
- Outside workspace → tools are blocked, use shell:
  - PowerShell: `Set-Content -Path '<path>' -Value '<text>' -Encoding UTF8`
  - bash: `printf '%s' '<text>' > '<path>'`
  - Writing outside the workspace changes things beyond the project; if it risks overwriting, ask the user first.

## Iron rules
- Inside workspace = tools, outside = shell. Keep them separate.
- Get it right the first time. On a syntax failure, switch to the correct shell once. Never cycle through variants.
