# Design Handoff Patterns

> Patterns for creating CDK projects from a design skill output (e.g. `design-aws`).
> These patterns extend the base patterns in other reference files.

---

## Reading the Design Doc

When receiving a handoff, read `designs/<app-name>/design.md` and extract:

| Design Doc Section | CDK Output |
|-------------------|------------|
| App Identity | `config/*/env.ts` (IntraEnvConfig per env) |
| Services table | `config/types.ts` (ServiceConfig[]), `config/*/services.ts` |
| Environment Matrix | per-env folders + enabled flags |
| Existing Infrastructure | `config/dev/vpc.ts`, `config/dev/alb.ts` with existing IDs |
| CloudFront Behaviors | `config/*/cloudfront.ts`, `lib/cloudfront-stack.ts` |
| SG Rules | auto-generated in `lib/alb-stack.ts`, `lib/service-stack.ts` |
| IAM Roles | `lib/service-stack.ts` (execution role + task role) |
| DNS/Domains | `config/*/dns.ts`, `lib/dns-stack.ts` |
| CDK Config Values | copy directly into config files |

Project output path: `projects/<app-name>/`

---

## Multi-Service Config Pattern

### Types

```typescript
// config/types.ts
export interface ServiceConfig {
  name: string;
  type: 'api' | 'frontend' | 'worker';
  port: number;
  healthCheckPath: string;
  pathPattern: string;
  cacheBehavior: 'caching-optimized' | 'caching-disabled';
}

export interface ServicesConfig {
  enabled: boolean;
  services: ServiceConfig[];
}
```

### Per-Environment Config

```typescript
// config/dev/services.ts
import { ServicesConfig } from '../types';

export const devServices: ServicesConfig = {
  enabled: true,
  services: [
    {
      name: 'api',
      type: 'api',
      port: 3000,
      healthCheckPath: '/health',
      pathPattern: '/base-path/api/*',
      cacheBehavior: 'caching-disabled',
    },
    {
      name: 'frontend',
      type: 'frontend',
      port: 4200,
      healthCheckPath: '/base-path',
      pathPattern: '/base-path/*',
      cacheBehavior: 'caching-optimized',
    },
  ],
};
```

### Stack Usage

```typescript
// lib/service-stack.ts
for (const svc of props.config.services) {
  const taskDef = new ecs.FargateTaskDefinition(this, `${svc.name}TaskDef`, {
    cpu: props.config.containerSpec.cpu,
    memoryLimitMiB: props.config.containerSpec.memory,
    executionRole,
    taskRole,
  });

  taskDef.addContainer(svc.name, {
    image: ecs.ContainerImage.fromEcrRepository(repo, 'latest'),
    portMappings: [{ containerPort: svc.port }],
    logging: ecs.LogDrivers.awsLogs({ streamPrefix: svc.name }),
  });

  new ecs.FargateService(this, `${svc.name}Service`, {
    cluster,
    taskDefinition: taskDef,
    desiredCount: props.config.containerSpec.desiredCount,
    serviceName: `${props.config.prefix}-ecs-${svc.name}`,
  });
}
```

---

## Existing VPC Pattern (non-prod)

When design doc specifies `VPC: existing`, use `Vpc.fromVpcAttributes`.

### Types

```typescript
// config/types.ts
export interface VpcConfig {
  enabled: boolean;  // true = create new, false = use existing
  // When enabled = true (dedicated)
  cidr?: string;
  maxAzs?: number;
  natGateways?: number;
  // When enabled = false (existing)
  existing?: {
    vpcId: string;
    containerSubnetIds: string[];
    publicSubnetIds: string[];
    privateSubnetIds?: string[];
  };
}
```

### Per-Environment Config

```typescript
// config/dev/vpc.ts — existing
export const devVpc: VpcConfig = {
  enabled: false,
  existing: {
    vpcId: 'vpc-0abc1234def567890',
    containerSubnetIds: [
      'subnet-0aaa111122223333a',
      'subnet-0bbb444455556666b',
      'subnet-0ccc777788889999c',
    ],
    publicSubnetIds: [
      'subnet-0ddd000011112222d',
      'subnet-0eee333344445555e',
      'subnet-0fff666677778888f',
    ],
  },
};

// config/prod/vpc.ts — dedicated
export const prodVpc: VpcConfig = {
  enabled: true,
  cidr: '10.0.0.0/16',
  maxAzs: 3,
  natGateways: 3,
};
```

### Stack Usage

```typescript
// lib/vpc-stack.ts
let vpc: ec2.IVpc;

if (props.config.vpc.enabled) {
  vpc = new ec2.Vpc(this, 'Vpc', {
    ipAddresses: ec2.IpAddresses.cidr(props.config.vpc.cidr!),
    maxAzs: props.config.vpc.maxAzs!,
    natGateways: props.config.vpc.natGateways!,
  });
} else {
  vpc = ec2.Vpc.fromVpcAttributes(this, 'Vpc', {
    vpcId: props.config.vpc.existing!.vpcId,
    availabilityZones: ['a', 'b', 'c'].map(az => `${this.region}${az}`),
    privateSubnetIds: props.config.vpc.existing!.containerSubnetIds,
    publicSubnetIds: props.config.vpc.existing!.publicSubnetIds,
  });
}
```

---

## Existing ALB Pattern (non-prod)

### Types

```typescript
// config/types.ts
export interface AlbConfig {
  enabled: boolean;  // true = create new, false = use existing
  // When enabled = true
  scheme?: 'internet-facing' | 'internal';
  certificateArn?: string;
  // When enabled = false
  existing?: {
    albArn: string;
    listenerArn: string;
  };
  // Shared
  basePath: string;
  healthCheck: {
    interval: number;
    healthyThreshold: number;
    unhealthyThreshold: number;
  };
}
```

### Stack Usage

```typescript
// lib/alb-stack.ts
let alb: elbv2.IApplicationLoadBalancer;
let listener: elbv2.IApplicationListener;

if (props.config.alb.enabled) {
  alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
    vpc,
    internetFacing: props.config.alb.scheme === 'internet-facing',
    loadBalancerName: `${props.config.prefix}-alb`,
  });
  listener = alb.addListener('Listener', { port: 443, certificates: [cert] });
} else {
  alb = elbv2.ApplicationLoadBalancer.fromApplicationLoadBalancerAttributes(
    this, 'Alb', {
      loadBalancerArn: props.config.alb.existing!.albArn,
      securityGroupId: '', // looked up separately if needed
    },
  );
  listener = elbv2.ApplicationListener.fromApplicationListenerAttributes(
    this, 'Listener', {
      listenerArn: props.config.alb.existing!.listenerArn,
      securityGroup: ec2.SecurityGroup.fromSecurityGroupId(this, 'AlbSg', ''),
    },
  );
}
```

---

## CloudFront Multi-Behavior Pattern

### Types

```typescript
// config/types.ts
export interface CloudFrontBehaviorConfig {
  pathPattern: string;
  originService: string;
  cachePolicy: 'caching-optimized' | 'caching-disabled';
  priority: number;
}

export interface CloudFrontConfig {
  enabled: boolean;
  domainName: string;
  behaviors: CloudFrontBehaviorConfig[];
  wafEnabled: boolean;
  wafRules?: string[];
  wafRateLimit?: number;
}
```

### Stack Usage

```typescript
// lib/cloudfront-stack.ts
const distribution = new cloudfront.Distribution(this, 'Distribution', {
  defaultBehavior: {
    origin: new origins.LoadBalancerV2Origin(alb),
    cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
  },
  additionalBehaviors: Object.fromEntries(
    props.config.behaviors
      .filter(b => b.priority > 0)
      .map(b => [
        b.pathPattern,
        {
          origin: new origins.LoadBalancerV2Origin(alb),
          cachePolicy: b.cachePolicy === 'caching-disabled'
            ? cloudfront.CachePolicy.CACHING_DISABLED
            : cloudfront.CachePolicy.CACHING_OPTIMIZED,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
      ])
  ),
  domainNames: [props.config.domainName],
  certificate: acmCert,
  webAclId: props.config.wafEnabled ? wafAcl.attrArn : undefined,
});
```

---

## Domain Per Environment Pattern

### Types

```typescript
// config/types.ts
export interface DnsConfig {
  enabled: boolean;
  domainName: string;
  hostedZoneId: string;
  certificateStrategy: 'create-new' | 'existing';
  certificateArn?: string;
}
```

### Per-Environment Config

```typescript
// config/dev/dns.ts
export const devDns: DnsConfig = {
  enabled: true,
  domainName: 'my-app-dev.nonprod-domain.example',
  hostedZoneId: 'Z0123456789EXAMPLE',
  certificateStrategy: 'create-new',
};

// config/prod/dns.ts
export const prodDns: DnsConfig = {
  enabled: true,
  domainName: 'my-app.prod-domain.example',
  hostedZoneId: 'Z9876543210EXAMPLE',
  certificateStrategy: 'create-new',
};
```

---

## Security Group Auto-Generation

SG rules are derived from services config — not manually configured.

```typescript
// lib/service-stack.ts (or lib/alb-stack.ts)
const sgAlb = new ec2.SecurityGroup(this, 'SgAlb', {
  vpc,
  securityGroupName: `${props.config.prefix}-sg-alb`,
  description: 'ALB security group',
});
sgAlb.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), 'HTTPS from internet');

const sgEcs = new ec2.SecurityGroup(this, 'SgEcs', {
  vpc,
  securityGroupName: `${props.config.prefix}-sg-ecs`,
  description: 'ECS tasks security group',
});

// Auto-derive from services
for (const svc of props.config.services) {
  sgAlb.addEgressRule(sgEcs, ec2.Port.tcp(svc.port), `To ${svc.name}`);
  sgEcs.addIngressRule(sgAlb, ec2.Port.tcp(svc.port), `${svc.name} from ALB`);
}

// ECS outbound for ECR, CloudWatch, external APIs
sgEcs.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), 'HTTPS outbound');
```

---

## IAM Roles Pattern

### Execution Role (standard — same for all services)

```typescript
const executionRole = new iam.Role(this, 'ExecutionRole', {
  roleName: `${props.config.prefix}-ecs-execution-role`,
  assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
  managedPolicies: [
    iam.ManagedPolicy.fromAwsManagedPolicyName(
      'service-role/AmazonECSTaskExecutionRolePolicy',
    ),
  ],
});

// If secrets are used
if (props.config.secrets && props.config.secrets.length > 0) {
  executionRole.addToPolicy(new iam.PolicyStatement({
    actions: ['secretsmanager:GetSecretValue'],
    resources: props.config.secrets.map(s => s.arn),
  }));
}
```

### Task Role (per-app — custom permissions)

```typescript
const taskRole = new iam.Role(this, 'TaskRole', {
  roleName: `${props.config.prefix}-ecs-task-role`,
  assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
});

// Add permissions from design doc Section 12
// Example: if app needs S3 access
// taskRole.addToPolicy(new iam.PolicyStatement({
//   actions: ['s3:GetObject', 's3:PutObject'],
//   resources: ['arn:aws:s3:::bucket-name/*'],
// }));
```

---

## WAF Pattern (pre-prod/prod only)

```typescript
// lib/waf-stack.ts
const webAcl = new wafv2.CfnWebACL(this, 'WebAcl', {
  name: `${props.config.prefix}-waf`,
  scope: 'CLOUDFRONT',
  defaultAction: { allow: {} },
  rules: [
    ...props.config.wafRules.map((rule, idx) => ({
      name: rule,
      priority: idx,
      overrideAction: { none: {} },
      statement: {
        managedRuleGroupStatement: { vendorName: 'AWS', name: rule },
      },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: rule,
      },
    })),
    {
      name: 'RateLimit',
      priority: 100,
      action: { block: {} },
      statement: {
        rateBasedStatement: {
          limit: props.config.wafRateLimit,
          aggregateKeyType: 'IP',
        },
      },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'RateLimit',
      },
    },
  ],
  visibilityConfig: {
    sampledRequestsEnabled: true,
    cloudWatchMetricsEnabled: true,
    metricName: `${props.config.prefix}-waf`,
  },
});
```

---

## Stacks to Generate

Based on a typical AWS service design doc:

| Stack | File | Condition |
|-------|------|-----------|
| VPC | `lib/vpc-stack.ts` | when vpc.enabled = true (prod/pre-prod) |
| ALB | `lib/alb-stack.ts` | when alb.enabled = true |
| ECS Cluster | `lib/cluster-stack.ts` | always |
| ECS Services | `lib/service-stack.ts` | always (loops over services) |
| ECR | `lib/ecr-stack.ts` | always (one repo per service) |
| CloudFront | `lib/cloudfront-stack.ts` | when cloudfront.enabled = true |
| WAF | `lib/waf-stack.ts` | when waf.enabled = true (pre-prod/prod) |
| DNS | `lib/dns-stack.ts` | when dns.enabled = true |
