# Multi-Environment Config Pattern & TypeScript Best Practices

> Source: AWS Prescriptive Guidance — "Best practices for using the AWS CDK in TypeScript to create IaC projects"
>
> Config-driven patterns are based on our project's proven three-layer architecture.

---

## Config-Driven Multi-Environment Pattern

### Core Principle

All environment-specific values live in `config/`. Stacks in `lib/` receive configuration through props — they never read environment variables or CDK context directly.

### IntraEnvConfig — Shared Environment Metadata

Each environment folder contains an `env.ts` that defines metadata shared across all resource configs in that environment. This avoids duplicating `envName`, `prefix`, `account`, and `region` in every resource file.

```typescript
// config/types.ts
export interface IntraEnvConfig {
  envName: string;
  envSuffix: string;
  prefix: string;
  projectName: string;
  account: string;
  region: string;
  deletionProtection: boolean;
  enableExecuteCommand: boolean;
  containerSpec: { cpu: number; memory: number; desiredCount: number };
  ecrRemovalPolicy: 'retain' | 'destroy';
  tags: Record<string, string>;
}
```

```typescript
// config/dev/env.ts
import { IntraEnvConfig } from '../types';
import { mergeTags } from '../shared/tags';

export const devEnv: IntraEnvConfig = {
  envName: 'dev',
  envSuffix: 'Dev',
  prefix: 'MyProjectDev',
  projectName: 'MyProject',
  account: '123456789012',
  region: 'ap-southeast-1',
  deletionProtection: false,
  enableExecuteCommand: true,
  containerSpec: { cpu: 256, memory: 512, desiredCount: 1 },
  ecrRemovalPolicy: 'destroy',
  tags: mergeTags({ Environment: 'dev' }),
};
```

### Tagging Strategy — Base Tags + Per-Environment Merge

Tags are managed through a shared helper in `config/shared/tags.ts`. Base tags (Project, Owner, Team, ManagedBy) are defined once and shared across all environments. Each environment merges its own tags on top — env-specific tags override base tags when keys collide.

```typescript
// config/shared/tags.ts
export const baseTags: Record<string, string> = {
  Project: 'my-project',
  Owner: 'TeamLead',
  Team: 'Platform',
  ManagedBy: 'cdk',
};

/** Merge base tags with env-specific tags — env tags override base */
export function mergeTags(envTags: Record<string, string>): Record<string, string> {
  return { ...baseTags, ...envTags };
}
```

```typescript
// config/dev/env.ts
import { mergeTags } from '../shared/tags';

export const devEnv: IntraEnvConfig = {
  // ...
  tags: mergeTags({ Environment: 'dev' }),
};
```

Tags are applied globally in `bin/app.ts` via `cdk.Tags.of(app).add()`, which propagates to every resource in every stack:

```typescript
// bin/app.ts
for (const [key, value] of Object.entries(config.tags)) {
  cdk.Tags.of(app).add(key, value);
}
```

This ensures all AWS resources are consistently tagged without any per-stack tagging logic.

### Per-Resource Config Files

Each resource type gets its own file. The resource config file imports `IntraEnvConfig` values when needed (e.g., for naming or deletion policies):

```typescript
// config/dev/aurora.ts
import { AuroraConfig } from '../types';
import { devEnv } from './env';

export const devAurora: AuroraConfig = {
  enabled: true,
  clusterIdentifier: `${devEnv.projectName}-${devEnv.envName}-aurora`,
  engine: 'aurora-postgresql',
  engineVersion: '15.4',
  databaseName: 'appdb',
  port: 5432,
  masterUsername: 'dbadmin',
  secretName: `${devEnv.prefix}/aurora/master`,
  ssmPrefix: `/${devEnv.projectName}/${devEnv.envName}/aurora`,
  subnetType: 'private',
  minCapacity: 0.5,
  maxCapacity: 2,
  enableReader: false,
  backupRetention: 7,
  deletionProtection: devEnv.deletionProtection,
  storageEncrypted: true,
  removalPolicy: 'destroy',
};
```

### Environment Assembly

Each environment's `index.ts` merges all resource configs into a single `EnvironmentConfig`:

```typescript
// config/dev/index.ts
import { EnvironmentConfig } from '../types';
import { devEnv } from './env';
import { devVpc } from './vpc';
import { devAlb } from './alb';
import { devEcr } from './ecr';
import { devCluster } from './cluster';
import { devServices } from './services';
import { devDns } from './dns';
import { devRedis } from './redis';
import { devAurora } from './aurora';

export const devConfig: EnvironmentConfig = {
  envName: devEnv.envName,
  prefix: devEnv.prefix,
  account: devEnv.account,
  region: devEnv.region,
  vpc: devVpc,
  ecr: devEcr,
  alb: devAlb,
  cluster: devCluster,
  services: devServices,
  dns: devDns,
  redis: devRedis,
  aurora: devAurora,
  tags: devEnv.tags,
};
```

### Enabled-Flag Pattern in `bin/app.ts`

Every resource config interface **must** include `enabled: boolean` as its first property. This is the single switch that controls whether a stack is created — no code changes in `lib/` or `bin/` are needed to enable or disable a resource for a specific environment.

#### Config Side (Producer)

In `config/types.ts`, every resource interface starts with `enabled`:

```typescript
export interface VpcConfig {
  enabled: boolean;   // ← always first property
  vpcId: string;
  // ...
}

export interface AlbConfig {
  enabled: boolean;
  albName: string;
  // ...
}

export interface RedisConfig {
  enabled: boolean;
  cacheName: string;
  // ...
}
```

In each environment's resource config, set `enabled` to `true` or `false`:

```typescript
// config/dev/redis.ts — Redis enabled in dev
export const devRedis: RedisConfig = {
  enabled: true,
  cacheName: `${devEnv.projectName}-${devEnv.envName}`,
  // ...
};

// config/sandbox/redis.ts — Redis disabled in sandbox (hypothetical)
export const sandboxRedis: RedisConfig = {
  enabled: false,
  cacheName: '',   // placeholder — never used when disabled
  // ...
};
```

#### App Side (Consumer)

In `bin/app.ts`, every stack instantiation is guarded by its `enabled` flag:

```typescript
// Simple guard — independent stack
if (config.redis.enabled) {
  new RedisStack(app, `${config.prefix}RedisStack`, { env: cdkEnv, config });
}
```

#### Dependency Chains

Some stacks depend on other stacks. Use `let ... | undefined` and combine enabled checks:

```typescript
// ALB and Cluster are independent
let albStack: AlbStack | undefined;
if (config.alb.enabled) {
  albStack = new AlbStack(app, `${config.prefix}AlbStack`, { env: cdkEnv, config });
}

let clusterStack: ClusterStack | undefined;
if (config.cluster.enabled) {
  clusterStack = new ClusterStack(app, `${config.prefix}ClusterStack`, { env: cdkEnv, config });
}

// Services require BOTH ALB and Cluster to exist
if (config.services.enabled && albStack && clusterStack) {
  for (const svc of config.services.items) {
    new ServiceStack(app, `${config.prefix}${svc.id}Stack`, {
      env: cdkEnv,
      config,
      serviceConfig: svc,
      albConstruct: albStack.albConstruct,
      ecsClusterConstruct: clusterStack.ecsClusterConstruct,
    });
  }
}

// DNS requires ALB
if (config.dns.enabled && albStack) {
  new DnsStack(app, `${config.prefix}DnsStack`, {
    env: cdkEnv,
    config,
    albConstruct: albStack.albConstruct,
  });
}
```

#### Rules

- **Every** resource config interface must have `enabled: boolean` as the first property.
- **Never** use `if (envName === 'prod')` to decide whether to create a stack. Use `enabled` flags only.
- When a stack depends on another stack, check **both** the `enabled` flag **and** the existence of the upstream stack variable (`&& albStack`).
- Disabled resources should still have valid (but minimal/placeholder) config values so that `types.ts` is satisfied.

### Adding a New Environment

1. Create `config/[newenv]/` folder
2. Copy an existing env folder (e.g., `dev/`) as a starting point
3. Update `env.ts` with the new environment's metadata
4. Adjust each resource config file as needed
5. Register in `config/environments.ts`:
   ```typescript
   import { newenvConfig } from './newenv';
   export const envConfigs: Record<string, EnvironmentConfig> = {
     sandbox: sandboxConfig,
     dev: devConfig,
     newenv: newenvConfig,  // ← add here
   };
   ```
6. Deploy: `cdk deploy --all -c env=newenv`

### Adding a New Resource Type

1. Define the interface in `config/types.ts`
2. Add the property to `EnvironmentConfig`
3. Create `config/[env]/[resource].ts` for each environment
4. Import and wire it in each `config/[env]/index.ts`
5. Create `lib/[resource]-stack.ts`
6. Add the enabled-flag guard in `bin/app.ts`
7. Create `test/[resource]-stack.test.ts`

---

## Follow TypeScript Best Practices

TypeScript is a language that extends the capabilities of JavaScript. It's a strongly typed and object-oriented language. You can use TypeScript to specify the types of data being passed within your code and has the ability to report errors when the types don't match. This section provides an overview of TypeScript best practices.

### Describe Your Data

You can use TypeScript to describe the shape of objects and functions in your code. Using the `any` type is equivalent to opting out of type checking for a variable. We recommend that you avoid using `any` in your code. Here is an example.

```typescript
type Result = "success" | "failure"

function verifyResult(result: Result) {
    if (result === "success") {
        console.log("Passed");
    } else {
        console.log("Failed")
    }
}
```

### Use Enums

You can use enums to define a set of named constants and define standards that can be reused in your code base. We recommend that you export your enums one time at the global level, and then let other classes import and use the enums. Assume that you want to create a set of possible actions to capture the events in your code base. TypeScript provides both numeric and string-based enums. The following example uses an enum.

```typescript
enum EventType {
    Create,
    Delete,
    Update
}

class InfraEvent {
    constructor(event: EventType) {
        if (event === EventType.Create) {
            // Call for other function
            console.log(`Event Captured :${event}`);
        }
    }
}

let eventSource: EventType = EventType.Create;
const eventExample = new InfraEvent(eventSource)
```

### Use Interfaces

An interface is a contract for the class. If you create a contract, then your users must comply with the contract. In the following example, an interface is used to standardize the props and ensure that callers provide the expected parameter when using this class.

```typescript
import { Stack, App } from "aws-cdk-lib";
import { Construct } from "constructs";

interface BucketProps {
    name: string;
    region: string;
    encryption: boolean;
}

class S3Bucket extends Stack {
    constructor(scope: Construct, props: BucketProps) {
        super(scope);
        console.log(props.name);
    }
}

const app = App();
const myS3Bucket = new S3Bucket(app, {
    name: "amzn-s3-demo-bucket",
    region: "us-east-1",
    encryption: false
})
```

Some properties can only be modified when an object is first created. You can specify this by putting `readonly` before the name of the property, as the following example shows.

```typescript
interface Position {
    readonly latitude: number;
    readonly longitute: number;
}
```

### Extend Interfaces

Extending interfaces reduces duplication, because you don't have to copy the properties between interfaces. Also, the reader of your code can easily understand the relationships in your application.

```typescript
interface BaseInterface{
    name: string;
}
interface EncryptedVolume extends BaseInterface{
    keyName: string;
}
interface UnencryptedVolume extends BaseInterface {
    tags: string[];
}
```

### Avoid Empty Interfaces

We recommend that you avoid empty interfaces due to the potential risks they create. In the following example, there's an empty interface called `BucketProps`. The `myS3Bucket1` and `myS3Bucket2` objects are both valid, but they follow different standards because the interface doesn't enforce any contracts. The following code will compile and print the properties but this introduces inconsistency in your application.

```typescript
interface BucketProps {}

class S3Bucket implements BucketProps {
    constructor(props: BucketProps){
        console.log(props);
    }
}

const myS3Bucket1 = new S3Bucket({
    name: "amzn-s3-demo-bucket",
    region: "us-east-1",
    encryption: false,
});

const myS3Bucket2 = new S3Bucket({
    name: "amzn-s3-demo-bucket",
});
```

### Use Factories

In an Abstract Factory pattern, an interface is responsible for creating a factory of related objects without explicitly specifying their classes. For example, you can create a Lambda factory for creating Lambda functions. Instead of creating a new Lambda function within your construct, you're delegating the creation process to the factory.

### Use Destructuring on Properties

Destructuring, introduced in ECMAScript 6 (ES6), is a JavaScript feature that gives you the ability to extract multiple pieces of data from an array or object and assign them to their own variables.

```typescript
const object = {
    objname: "obj",
    scope: "this",
};

const oName = object.objname;
const oScop = object.scope;

const { objname, scope } = object;
```

### Define Standard Naming Conventions

Enforcing a naming convention keeps the code base consistent and reduces overhead when thinking about how to name a variable. We recommend the following:

- Use **camelCase** for variable and function names.
- Use **UPPER_CASE** for global constants to clearly indicate immutable compile-time values.
- Use **PascalCase** for class names and interface names.
- Use **camelCase** for interface members.
- Use **PascalCase** for type names and enum names.
- Name files with **camelCase** (for example, `ebsVolumes.tsx` or `storage.ts`)

The following shows examples of these recommended naming conventions:

```typescript
// Variables and functions
const userName = 'john';
function getUserData() { }

// Global constants
const MAX_RETRY_ATTEMPTS = 3;
const API_BASE_URL = 'https://api.example.com';

// Classes and interfaces
class DatabaseConnection { }
interface UserProfile { }

// Types and enums
type ResponseStatus = 'success' | 'error';
enum HttpStatusCode { }
```

### Don't Use the `var` Keyword

The `let` statement is used to declare a local variable in TypeScript. It's similar to the `var` keyword, but it has some restrictions in scoping compared to the `var` keyword. A variable declared in a block with `let` is only available for use within that block. The `var` keyword cannot be block-scoped, which means it can be accessed outside a particular block (represented by `{}`) but not outside of the function it's defined in. You can redeclare and update `var` variables. It's a best practice to avoid using the `var` keyword.

### Consider Using ESLint and Prettier

ESLint statically analyzes your code to quickly find issues. You can use ESLint to create a series of assertions (called *lint rules*) that define how your code should look or behave. ESLint also has auto-fixer suggestions to help you improve your code. Finally, you can use ESLint to load in lint rules from shared plugins.

Prettier is a well-known code formatter that supports a variety of different programming languages. You can use Prettier to set your code style so that you can avoid manually formatting your code. After installation, you can update your `package.json` file and run the `npm run format` and `npm run lint` commands.

The following example shows you how to enable ESLint and the Prettier formatter for your AWS CDK project.

```json
"scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "test": "jest",
    "cdk": "cdk",
    "lint": "eslint --ext .js,.ts .",
    "format": "prettier --ignore-path .gitignore --write '**/*.+(js|ts|json)'"
}
```

### Use Access Modifiers

The `private` modifier in TypeScript limits visibility to the same class only. When you add the private modifier to a property or method, you can access that property or method within the same class.

The `public` modifier allows class properties and methods to be accessible from all locations. If you don't specify any access modifiers for properties and methods, they will take the public modifier by default.

The `protected` modifier allows properties and methods of a class to be accessible within the same class and within subclasses. Use the protected modifier when you expect to create subclasses in your AWS CDK application.

### Use Utility Types

Utility types in TypeScript are predefined type functions that perform transformations and operations on existing types. This helps you create new types based on existing types. For example, you can change or extract properties, make properties optional or required, or create immutable versions of types. By using utility types, you can define more precise types and catch potential errors at compile time.

#### `Partial<Type>`

`Partial` marks all members of an input type `Type` as optional. This utility returns a type that represents all subsets of a given type. The following is an example of `Partial`.

```typescript
interface Dog {
  name: string;
  age: number;
  breed: string;
  weight: number;
}

let partialDog: Partial<Dog> = {};
```

#### `Required<Type>`

`Required` does the opposite of `Partial`. It makes all members of an input type `Type` non-optional (in other words, required). The following is an example of `Required`.

```typescript
interface Dog {
  name: string;
  age: number;
  breed: string;
  weight?: number;
}

let dog: Required<Dog> = {
  name: "scruffy",
  age: 5,
  breed: "labrador",
  weight: 55 // "Required" forces weight to be defined
};
```
