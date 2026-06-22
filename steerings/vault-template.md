# Obsidian Vault Template (portable)

The knowledge structure this memory system writes into. Used to scaffold a user's vault on
first run and as the format reference for captured entries. Works with Obsidian + any AI tool.
Language: English (saves tokens, better AI comprehension).

## Directory structure

```
<vault>/
├─ _system/                 ← vault's own reference (this template lives here after init)
│  └─ vault-template.md
├─ index.md                 ← entry point / table of contents
├─ insights/                ← atomic reusable notes (3-5 lines each)
│  └─ {slug}.md
├─ errors/                  ← cross-project errors
│  ├─ index.md              ← error lookup table
│  └─ {slug}.md
├─ projects/                ← one self-contained folder per project
│  └─ {project-name}/
│     ├─ _index.md
│     ├─ hot.md             ← current state (≤30 lines)
│     ├─ domain/{topic}/{slug}.md
│     └─ logs/
│        ├─ errors/{YYYYMMDD-slug}.md
│        ├─ decisions/{YYYYMMDD-slug}.md
│        └─ iterations/{slug}.md
├─ reference/               ← shared (glossary, cheatsheets)
├─ raw/                     ← unprocessed (AI: do NOT read)
└─ archive/                 ← retired (AI: do NOT read)
```

## Naming
- Folders & files: lowercase-kebab, max 50 chars, no spaces, `.md`.
- Date prefix `YYYYMMDD-` ONLY for chronological logs (errors/decisions inside `projects/*/logs/`).
- NO date prefix for `insights/`, root `errors/`, or domain pages (the date lives inside the file).
- Tags: `#lowercase`.

## Templates

### `insights/{slug}.md`
```
# {insight as a statement}

{2-4 sentences with evidence}

**Evidence**: {data/source}
**So what**: {action to take}

Tags: #topic #topic
```

### `errors/{slug}.md`
```
# ❌ {what happened}

Date: YYYY-MM-DD
Category: logic | data | config | integration | os
Severity: 🔴 Critical | 🟡 Medium | 🟢 Low

## What
{2-3 sentences}

## Root Cause
{the real reason}

## Fix
{what was done}

## Lesson
{one sentence}
```

### `index.md` (root)
```
# Knowledge Index

> AI: read this → follow links → never read raw/ or archive/

## Projects
| Project | Status | Hot |
|---------|--------|-----|

## Recent Insights
| Insight | Tags |
|---------|------|

## Errors (cross-project)
→ [errors/index.md](./errors/index.md)

## Reference
| Page | Use When |
|------|----------|
```

### `errors/index.md`
```
# Error Index

> AI: scan this table first; open the linked file only if it matches.

| Error | Cause | Fix | File |
|-------|-------|-----|------|
```

### `projects/{repo}/logs/decisions/{YYYYMMDD-slug}.md`
```
# 🔀 {decision title}

Date: YYYY-MM-DD

## Context
{why this decision was needed}

## Options
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

## Chose
**{X}** because {reason}.
```

### `projects/{repo}/logs/iterations/{slug}.md`
```
# {what changed}

Date: YYYY-MM-DD

## Before
{prior state}

## Change
{what was done and why}

## After
{new state / result}
```

### `projects/{repo}/hot.md` (≤30 lines; overflow → logs/iterations/)
```
# 🔥 {project} — Current State

Updated: YYYY-MM-DD

## Status
- **Goal**: {one sentence}
- **Phase**: research | building | testing | live

## Next Actions (max 5)
- [ ] ...

## Recent (7 days)
- ✅ {win}
- ❌ {failure} → see logs/errors/...
```

### Domain pages `projects/{repo}/domain/{topic}/{slug}.md`
Free-form reference documents — full design specs, config schemas, deep knowledge.
No fixed template; use clear headed sections and tables. Written deliberately for knowledge
worth keeping long-term, not auto-logged from quick tasks.
