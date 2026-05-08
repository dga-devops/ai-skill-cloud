# Project Structure & Code Organization

> Based on AWS Prescriptive Guidance, adapted to our project's three-layer architecture.

## Three-Layer Architecture

The project separates concerns into three distinct layers:

| Layer | Directory | Responsibility | Contains AWS Constructs? |
|-------|-----------|---------------|------------------------|
| **Data** | `config/` | Environment-specific values, interfaces, constants | ❌ Never |
| **Logic** | `lib/` | Stacks, constructs, AWS resource definitions | ✅ Yes |
| **Quality** | `test/` | Fine-grained assertion tests | ❌ Only test utilities |

The entry point `bin/app.ts` wires the data layer into the logic layer.

## Canonical Directory Structure

```
project-root/
├── bin/
│   └── app.ts                 # Entry point: load config → instantiate stacks
│
├── config/                    # ── DATA LAYER ──────────────────────────────
│   ├── types.ts               # All configuration interfaces (EnvironmentConfig, VpcConfig, etc.)
│   ├── environments.ts        # Environment registry: Record<string, EnvironmentConfig>
│   ├── index.ts               # getConfig(env) helper + re-exports
│   ├── shared/                # Constants shared across all environments
│   │   ├── tags.ts            # baseTags + mergeTags() helper
│   │   └── constants.ts
│   ├── sandbox/               # Per-environment folders
│   │   ├── index.ts           # Assembles all resource configs → EnvironmentConfig
│   │   ├── env.ts             # IntraEnvConfig (envName, prefix, account, region, tags)
│   │   ├── vpc.ts
│   │   ├── alb.ts
│   │   └── ...
│   ├── dev/
│   │   ├── index.ts
│   │   ├── env.ts
│   │   ├── vpc.ts
│   │   ├── alb.ts
│   │   ├── ecr.ts
│   │   ├── cluster.ts
│   │   ├── services.ts
│   │   ├── dns.ts
│   │   ├── redis.ts
│   │   └── aurora.ts
│   └── prod/
│       └── ...                # Same structure as dev
│
├── lib/                       # ── LOGIC LAYER ─────────────────────────────
│   ├── common/                # (optional) Shared aspects, extended L2 constructs
│   ├── alb-stack.ts           # One file per stack — flat layout
│   ├── aurora-stack.ts
│   ├── cluster-stack.ts
│   ├── dns-stack.ts
│   ├── ecr-stack.ts
│   ├── redis-stack.ts
│   └── service-stack.ts
│
├── test/                      # ── QUALITY LAYER ───────────────────────────
│   ├── alb-stack.test.ts      # One test file per stack
│   ├── aurora-stack.test.ts
│   ├── cluster-stack.test.ts
│   ├── ecr-stack.test.ts
│   ├── redis-stack.test.ts
│   └── config.test.ts         # Config validation tests
│
├── scripts/                   # Build/clean utilities
├── .gitignore
├── .eslintrc.json
├── .prettierrc
├── jest.config.js
├── tsconfig.json
├── cdk.json
├── ARCHITECTURE.md            # High-level architecture documentation
└── package.json
```

## Layer Details

### Data Layer (`config/`)

The config layer is a **pure TypeScript data layer** — it contains no AWS CDK constructs, no `import * as cdk from 'aws-cdk-lib'`, and no resource instantiation. It only exports typed configuration objects.

#### Key Files

**`config/types.ts`** — Central interface definitions for all resource configs:

```typescript
export interface IntraEnvConfig {
  envName: string;
  prefix: string;
  account: string;
  region: string;
  tags: Record<string, string>;
}

export interface VpcConfig {
  enabled: boolean;
  vpcId: string;
  // ...
}

export interface EnvironmentConfig {
  envName: string;
  prefix: string;
  account: string;
  region: string;
  vpc: VpcConfig;
  alb: AlbConfig;
  cluster: ClusterConfig;
  // ... one property per resource type
  tags: Record<string, string>;
}
```

**`config/[env]/env.ts`** — Shared metadata for one environment:

```typescript
import { IntraEnvConfig } from '../types';
import { mergeTags } from '../shared/tags';

const env: IntraEnvConfig = {
  envName: 'dev',
  prefix: 'MyProjectDev',
  account: '123456789012',
  region: 'ap-southeast-1',
  tags: mergeTags({ Environment: 'dev' }),
};
export { env as devEnv };
```

**`config/[env]/index.ts`** — Assembles per-resource configs into a single `EnvironmentConfig`:

```typescript
import { EnvironmentConfig } from '../types';
import { devEnv } from './env';
import { devVpc } from './vpc';
import { devAlb } from './alb';
// ... import each resource config

export const devConfig: EnvironmentConfig = {
  envName: devEnv.envName,
  prefix: devEnv.prefix,
  account: devEnv.account,
  region: devEnv.region,
  vpc: devVpc,
  alb: devAlb,
  // ... spread each resource config
  tags: devEnv.tags,
};
```

**`config/environments.ts`** — Registry of all environments:

```typescript
import { EnvironmentConfig } from './types';
import { sandboxConfig } from './sandbox';
import { devConfig } from './dev';

export const envConfigs: Record<string, EnvironmentConfig> = {
  sandbox: sandboxConfig,
  dev: devConfig,
};
```

**`config/index.ts`** — Public API with validation:

```typescript
import { envConfigs } from './environments';
import { EnvironmentConfig } from './types';

export function getConfig(env: string): EnvironmentConfig {
  const config = envConfigs[env];
  if (!config) {
    throw new Error(`Unknown environment: "${env}". Valid: ${Object.keys(envConfigs).join(', ')}`);
  }
  return config;
}
```

### Logic Layer (`lib/`)

Each stack is a single file in `lib/`. No nested subdirectories for stacks.

**Naming convention**: `[resource]-stack.ts` → `[Resource]Stack` class.

Every stack accepts `EnvironmentConfig` (or a subset) as props. Stacks never read environment variables or context directly — all data flows through config.

**Cross-stack references**: When a stack needs output from another stack (e.g., ServiceStack needs the ALB and ECS Cluster), pass the construct reference through props in `bin/app.ts`:

```typescript
// bin/app.ts
if (config.services.enabled && albStack && clusterStack) {
  new ServiceStack(app, `${config.prefix}ServiceStack`, {
    env: cdkEnv,
    config,
    albConstruct: albStack.albConstruct,
    ecsClusterConstruct: clusterStack.ecsClusterConstruct,
  });
}
```

### Entry Point (`bin/app.ts`)

The entry point is responsible for:

1. Reading the environment name from CDK context (`-c env=dev`)
2. Loading the validated config via `getConfig(env)`
3. Applying global tags
4. Instantiating stacks in dependency order, guarded by `enabled` flags
5. Applying cdk-nag Aspects when required

```typescript
#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { getConfig } from '../config';
import { EcrStack } from '../lib/ecr-stack';
import { AlbStack } from '../lib/alb-stack';
// ... other stack imports

const app = new cdk.App();
const envName = app.node.tryGetContext('env') ?? 'sandbox';
const config = getConfig(envName);
const cdkEnv = { account: config.account, region: config.region };

// Global tags
for (const [key, value] of Object.entries(config.tags)) {
  cdk.Tags.of(app).add(key, value);
}

// Instantiate stacks — always guard with enabled flags
if (config.ecr.enabled) {
  new EcrStack(app, `${config.prefix}EcrStack`, { env: cdkEnv, config });
}

let albStack: AlbStack | undefined;
if (config.alb.enabled) {
  albStack = new AlbStack(app, `${config.prefix}AlbStack`, { env: cdkEnv, config });
}

// ... more stacks in dependency order

// cdk-nag (enable for uat/preprod/prod)
// cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

### Quality Layer (`test/`)

One test file per stack. Tests use the ARRANGE → ACT → ASSERT pattern:

```typescript
import { Stack } from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';

test('ECR repository is created', () => {
  // ARRANGE
  const stack = new Stack();
  // ACT
  new EcrStack(stack, 'TestEcr', { config: testConfig });
  // ASSERT
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::ECR::Repository', 1);
});
```

## Why This Structure (vs. AWS Prescriptive Guidance)

The AWS Prescriptive Guidance document recommends a nested `lib/common/compute/lambda/` structure with factory patterns. Our structure differs intentionally:

| Aspect | AWS Prescriptive Guidance | Our Structure |
|--------|--------------------------|---------------|
| Config location | Mixed inside `lib/` | Separate `config/` at root |
| Config granularity | Not specified | One file per resource per env |
| Stack layout | Nested in `lib/common/` | Flat in `lib/` — one file per stack |
| Shared metadata | Not addressed | `IntraEnvConfig` pattern in `env.ts` |
| Stack instantiation | Not detailed | `enabled` flag guards in `bin/app.ts` |
| Design patterns | Factory + Chain of Responsibility | Direct L2 composition (simpler for our scale) |

**Rationale**: Our projects use L2 constructs directly without shared construct libraries. The flat layout is easier to navigate, and the clean config/lib separation prevents accidental coupling between data and infrastructure logic. The factory/nesting approach from the PDF is better suited for very large monorepo projects with shared construct libraries across multiple teams.

> **Note**: If the project grows to need shared custom constructs (e.g., an extended `SecureBucket`), place them in `lib/common/`. This folder is reserved for reusable constructs and CDK Aspects.
