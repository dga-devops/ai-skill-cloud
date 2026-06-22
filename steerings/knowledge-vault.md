# Knowledge Vault — how this vault is maintained

This vault is written to by AI assistants (Kiro, Copilot, Claude Code) as you work.
The actual capture rules live in each project's steering/instruction files — this doc is a
human-readable summary so the vault explains itself. It is NOT read by the AI at runtime.

## Where the real rules live (source of truth)
Bundled in the "steerings" set, copied into each project:
- Kiro → `.kiro/steering/memory-capture.md`
- Copilot → `.github/instructions/memory-capture.instructions.md`
- Claude Code / generic agents → `AGENTS.md`

## What gets written here
- `insights/{slug}.md` — atomic reusable lessons (3-5 lines)
- `errors/{slug}.md` + `errors/index.md` — cross-project bug/incident write-ups
- `projects/{repo}/...` — project-specific logs (errors / decisions / iterations), domain pages, `hot.md`
- Structure & entry formats → `_system/vault-template.md`

## Conventions
- English only; lowercase-kebab filenames (≤50 chars)
- Date prefix `YYYYMMDD-` ONLY for logs (errors/decisions); never for insights or domain pages
- Capture only what's worth remembering (hard bugs, real decisions, env gotchas, reusable workflows); skip trivial
- The vault is outside the workspace → AI writes via shell and updates indexes inline

## Do not
- Never read or write `raw/` or `archive/`
