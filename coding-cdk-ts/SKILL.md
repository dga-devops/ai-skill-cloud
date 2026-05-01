---
name: coding-cdk-ts
description: >
  Apply AWS Prescriptive Guidance for TypeScript CDK development. 
  Triggers when creating or refactoring AWS stacks, L2 constructs, 
  multi-environment configurations (sandbox/dev/sit/uat/preprod/prod),
  security scanning with cdk-nag, and unit testing with assertions. 
  Use for any task involving CloudFormation synthesis or AWS infrastructure architecture.
---

# coding-cdk-ts

You are an AWS CDK expert. You follow the "AWS Prescriptive Guidance" for TypeScript IaC projects. You prioritize security, scalability, and maintainability.

## Project Architecture

This project uses a **three-layer architecture** that cleanly separates data, logic, and quality:

```
project-root/
├── bin/
│   └── app.ts                 # Entry point: load config → instantiate stacks
├── config/                    # DATA LAYER — pure TypeScript data, no AWS constructs
│   ├── types.ts               # All configuration interfaces
│   ├── environments.ts        # Environment registry: Record<string, EnvironmentConfig>
│   ├── shared/                # Constants shared across all environments
│   └── [env]/                 # One folder per environment (sandbox, dev, uat, prod…)
│       ├── index.ts           # Merges per-resource configs into EnvironmentConfig
│       ├── env.ts             # IntraEnvConfig (envName, prefix, account, region, tags)
│       ├── vpc.ts             # VPC settings
│       ├── alb.ts             # ALB settings
│       └── …                  # One file per resource type
├── lib/                       # LOGIC LAYER — reusable stacks & constructs
│   ├── common/                # (optional) Shared aspects, extended L2 constructs
│   ├── network-stack.ts       # One file per stack — flat layout
│   └── database-stack.ts
├── test/                      # QUALITY LAYER — fine-grained assertion tests
│   ├── network-stack.test.ts  # One test file per stack
│   └── config.test.ts         # Config validation tests
├── scripts/                   # Build/clean utilities
├── .eslintrc.json
├── .prettierrc
├── jest.config.js
├── tsconfig.json
└── package.json
```

See `references/structure.md` for full details and rationale.

## Instructions

1. **Project Anatomy**: Follow the three-layer structure (config → lib → test). Config is a pure data layer at the project root — never place AWS constructs inside `config/`. See `references/structure.md`.
2. **Construct Selection**: Apply the "L2-First" rule. **Do not use L3 constructs** — compose L2 constructs manually instead. Use escape hatches to access L1 when L2 doesn't expose a feature. See `references/constructs.md`.
3. **Multi-Environment Config**: Every resource that varies per environment must be driven by `config/[env]/`. Use `enabled` flags to conditionally instantiate stacks in `bin/app.ts`. Use `IntraEnvConfig` to share env metadata across resource configs. See `references/config-pattern.md`.
4. **Security Enforcement**: 
   - Use `cdk-nag` with `AwsSolutionsChecks` as an Aspect on the app.
   - **Mandatory**: `uat`, `preprod`, and `prod` MUST have cdk-nag enabled.
   - See `references/security.md` for scanning tools and versioning practices.
5. **Testing Strategy**: Write fine-grained assertion tests (one test file per stack). Use the ARRANGE → ACT → ASSERT pattern with `Template.fromStack()`. See `references/testing.md`.

## Core Constraints

- **Zero Hardcoding**: Every value that changes per environment MUST come from `config/`. No magic strings in `lib/` or `bin/`.
- **Strict Typing**: No `any` types. Define explicit interfaces in `config/types.ts` for every resource config.
- **Naming**: camelCase for variables/functions/files, PascalCase for classes/interfaces, UPPER_CASE for global constants.
- **Enabled-Flag Guard**: Always check `config.[resource].enabled` before instantiating optional stacks in `bin/app.ts`.
- **No L3 Constructs**: Always prefer L2 constructs; do not use L3 patterns.
- **Flat Stack Layout**: One file per stack in `lib/`. No nested subdirectories for stacks.
- **One Config File Per Resource**: Each resource type gets its own file in `config/[env]/` (e.g., `vpc.ts`, `alb.ts`, `aurora.ts`).

---
> [!TIP]
> Need more details? Read:
> - `references/structure.md` — Project layout, layer responsibilities, config patterns
> - `references/constructs.md` — Construct hierarchy, L2-First rule, escape hatches, custom resources
> - `references/config-pattern.md` — TypeScript best practices, naming conventions, interfaces, utility types
> - `references/testing.md` — TDD approach, fine-grained assertions, unit test templates
> - `references/security.md` — cdk-nag, Checkov, documentation with TypeDoc, versioning & release
