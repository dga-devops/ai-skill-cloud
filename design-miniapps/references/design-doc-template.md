# Design Document Template

Use this template to generate the design document for each miniapp.
Replace `{{placeholder}}` with actual values from the checklist.

---

<!-- BEGIN TEMPLATE -->

# {{APP_NAME}} — Architecture Design

| Field | Value |
|-------|-------|
| App Name | {{APP_NAME}} |
| Description | {{DESCRIPTION}} |
| Owner | {{OWNER}} |
| Team | {{TEAM}} |
| Created | {{DATE}} |
| Environments | {{ENVIRONMENTS}} |
| Prod Spec | CPU {{PROD_CPU}} / Memory {{PROD_MEMORY}} MB |

---

## Architecture Overview

{{APP_NAME}} is a miniapp with {{SERVICE_COUNT}} service(s) deployed on ECS Fargate behind ALB with path-based routing. CloudFront serves as CDN with per-service cache behaviors{{#WAF_ENABLED}} and WAF for security (pre-prod/prod){{/WAF_ENABLED}}.

---

## Services

| Service | Type | Port | Path Pattern | CF Cache |
|---------|------|------|-------------|----------|
{{#SERVICES}}
| {{NAME}} | {{TYPE}} | {{PORT}} | `{{PATH_PATTERN}}` | {{CACHE_POLICY}} |
{{/SERVICES}}

---

## Domains

| Environment | Domain | Account | Tier |
|-------------|--------|---------|------|
{{#ENVIRONMENTS}}
| {{ENV}} | `{{DOMAIN}}` | `{{ACCOUNT_ID}}` | {{TIER}} |
{{/ENVIRONMENTS}}

---

## CloudFront Behaviors

| Priority | Path Pattern | Origin | Cache Policy |
|----------|-------------|--------|-------------|
{{#CF_BEHAVIORS}}
| {{PRIORITY}} | `{{PATH}}` | ALB -> {{SERVICE}} TG | {{CACHE_POLICY}} |
{{/CF_BEHAVIORS}}

---

## Resource List

### Core Resources (all environments)

| Resource Type | Name Pattern | Key Config |
|---------------|-------------|------------|
| ECS Cluster | `{{APP_NAME}}-{env}-ecs-cluster` | Fargate |
{{#SERVICES}}
| ECS Service ({{NAME}}) | `{{APP_NAME}}-{env}-ecs-{{NAME}}` | CPU: {{CPU}}, Mem: {{MEMORY}} |
| Target Group ({{NAME}}) | `{{APP_NAME}}-{env}-tg-{{NAME}}` | Port: {{PORT}}, Path: `{{PATH_PATTERN}}` |
| ECR ({{NAME}}) | `{{APP_NAME}}-{{NAME}}` | Tag: {{IMAGE_TAG_STRATEGY}} |
| Log Group ({{NAME}}) | `{{APP_NAME}}-{env}-logs-{{NAME}}` | Retention: per tier |
{{/SERVICES}}
| ALB | `{{APP_NAME}}-{env}-alb` | {{ALB_SCHEME}} |
| CloudFront | `{{APP_NAME}}-{env}-cf` | {{SERVICE_COUNT}} behaviors |
| Security Group (ALB) | `{{APP_NAME}}-{env}-sg-alb` | Ingress: 443 |
| Security Group (ECS) | `{{APP_NAME}}-{env}-sg-ecs` | Ingress: service ports from ALB SG |

### Conditional Resources

{{#WAF_ENABLED}}
| WAF WebACL | `{{APP_NAME}}-{env}-waf` | Rules: {{WAF_RULES}} |
{{/WAF_ENABLED}}
{{#DATABASE_ENABLED}}
| {{DATABASE_TYPE}} | `{{APP_NAME}}-{env}-{{DB_RESOURCE}}` | {{DB_CONFIG_SUMMARY}} |
{{/DATABASE_ENABLED}}
{{#CACHE_ENABLED}}
| ElastiCache | `{{APP_NAME}}-{env}-redis` | {{CACHE_NODE_TYPE}}, Nodes: {{CACHE_NODES}} |
{{/CACHE_ENABLED}}
{{#QUEUE_ENABLED}}
| SQS Queue | `{{APP_NAME}}-{env}-sqs-{{QUEUE_NAME}}` | Timeout: {{VISIBILITY_TIMEOUT}}s |
{{/QUEUE_ENABLED}}
{{#STORAGE_ENABLED}}
| S3 Bucket | `{{APP_NAME}}-{env}-s3-{{BUCKET_PURPOSE}}-{account}` | Versioning: {{VERSIONING}} |
{{/STORAGE_ENABLED}}

---

## Environment Matrix

| Config | dev | uat | pre-prod | prod |
|--------|-----|-----|----------|------|
| Account | {{DEV_ACCOUNT}} | {{UAT_ACCOUNT}} | {{PREPROD_ACCOUNT}} | {{PROD_ACCOUNT}} |
| Tier | non-prod | non-prod | pre-prod | prod |
| VPC | existing | existing | dedicated | dedicated |
| ALB | existing | existing | dedicated | dedicated |
| WAF | ❌ | ❌ | ✅ | ✅ |
| Multi-AZ | ❌ | ❌ | ❌ | ✅ |
| cdk-nag | ❌ | ✅ | ✅ | ✅ |
| Deletion protection | ❌ | ❌ | ✅ | ✅ |
| Execute command | ✅ | ✅ | ❌ | ❌ |
| CPU | {{NONPROD_CPU}} | {{NONPROD_CPU}} | {{PROD_CPU}} | {{PROD_CPU}} |
| Memory | {{NONPROD_MEM}} | {{NONPROD_MEM}} | {{PROD_MEM}} | {{PROD_MEM}} |
| Desired count | 1 | 1 | 1 | {{PROD_DESIRED}} |
| Log retention | 14d | 14d | 30d | 90d |
| ECR policy | destroy | destroy | retain | retain |
| Domain | {{DEV_DOMAIN}} | {{UAT_DOMAIN}} | {{PREPROD_DOMAIN}} | {{PROD_DOMAIN}} |

---

## CDK Config Values

### IntraEnvConfig (per environment)

```typescript
// Example: dev
{
  envName: 'dev',
  envSuffix: 'Dev',
  prefix: '{{APP_NAME_PASCAL}}Dev',
  projectName: '{{APP_NAME}}',
  account: '{{DEV_ACCOUNT}}',
  region: '{{REGION}}',
  deletionProtection: false,
  enableExecuteCommand: true,
  containerSpec: { cpu: {{NONPROD_CPU}}, memory: {{NONPROD_MEM}}, desiredCount: 1 },
  ecrRemovalPolicy: 'destroy',
  tags: mergeTags({ Environment: 'dev' }),
}
```

### Services Config

```typescript
{
  services: [
    {{#SERVICES}}
    {
      name: '{{NAME}}',
      type: '{{TYPE}}',
      port: {{PORT}},
      healthCheckPath: '{{HEALTH_CHECK_PATH}}',
      pathPattern: '{{PATH_PATTERN}}',
      cacheBehavior: '{{CACHE_POLICY}}',
    },
    {{/SERVICES}}
  ],
}
```

### CloudFront Config

```typescript
{
  enabled: true,
  behaviors: [
    {{#CF_BEHAVIORS}}
    {
      pathPattern: '{{PATH}}',
      originService: '{{SERVICE}}',
      cachePolicy: '{{CACHE_POLICY}}',
      priority: {{PRIORITY}},
    },
    {{/CF_BEHAVIORS}}
  ],
  wafEnabled: false, // true for pre-prod/prod
}
```

### DNS Config

```typescript
{
  nonProdBaseDomain: '{{NONPROD_BASE_DOMAIN}}',
  prodBaseDomain: '{{PROD_BASE_DOMAIN}}',
  domainPatterns: {
    'dev': '{{APP_NAME}}-dev.{{NONPROD_BASE_DOMAIN}}',
    'uat': '{{APP_NAME}}-uat.{{NONPROD_BASE_DOMAIN}}',
    'pre-prod': '{{APP_NAME}}-pre-prod.{{PROD_BASE_DOMAIN}}',
    'prod': '{{APP_NAME}}.{{PROD_BASE_DOMAIN}}',
  },
}
```

### VPC Config (dedicated — pre-prod/prod)

```typescript
{
  enabled: true, // false for non-prod (use existing)
  cidr: '{{CIDR}}',
  maxAzs: {{AZS}},
  natGateways: {{NAT_COUNT}}, // pre-prod: 1, prod: one-per-az
}
```

---

## Security Group Rules

### sg-alb (`{{APP_NAME}}-{env}-sg-alb`)

| Direction | Protocol | Port | Source/Destination | Purpose |
|-----------|----------|------|--------------------|---------|
| Inbound | TCP | 443 | 0.0.0.0/0 | HTTPS from internet/CloudFront |
{{#SERVICES}}
| Outbound | TCP | {{PORT}} | sg-ecs | Forward to {{NAME}} service |
{{/SERVICES}}

### sg-ecs (`{{APP_NAME}}-{env}-sg-ecs`)

| Direction | Protocol | Port | Source/Destination | Purpose |
|-----------|----------|------|--------------------|---------|
{{#SERVICES}}
| Inbound | TCP | {{PORT}} | sg-alb | {{NAME}} traffic from ALB |
{{/SERVICES}}
| Outbound | TCP | 443 | 0.0.0.0/0 | External API calls, ECR pull, CloudWatch |

---

## IAM Roles

### ECS Task Execution Role (`{{APP_NAME}}-{env}-ecs-execution-role`)

| Policy | Actions | Resource |
|--------|---------|----------|
| ECR Pull | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` | ECR repo ARN |
| CloudWatch Logs | `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` | Log group ARN |
{{#HAS_SECRETS}}
| Secrets | `secretsmanager:GetSecretValue` | Secret ARNs |
{{/HAS_SECRETS}}

### ECS Task Role (`{{APP_NAME}}-{env}-ecs-task-role`)

| Policy | Actions | Resource |
|--------|---------|----------|
{{#IAM_PERMISSIONS}}
| {{POLICY_NAME}} | {{ACTIONS}} | {{RESOURCE}} |
{{/IAM_PERMISSIONS}}
{{^IAM_PERMISSIONS}}
| (TBD) | TBD | TBD |
{{/IAM_PERMISSIONS}}

---

## Existing Infrastructure (non-prod)

| Resource | ID |
|----------|----|
{{#EXISTING_RESOURCES}}
| {{RESOURCE_TYPE}} | `{{RESOURCE_ID}}` |
{{/EXISTING_RESOURCES}}

---

## Diagrams

- Architecture diagram (DAC): [`diagram.yaml`](./diagram.yaml)
- Architecture diagram (Python): [`diagram.py`](./diagram.py)

Render:
```bash
awsdac diagram.yaml -o architecture.png
python diagram.py
```

---

## Handoff to CDK

Once approved, use `coding-cdk-ts` skill to:
1. Create project structure (three-layer architecture)
2. Generate `config/types.ts` from CDK Config Values
3. Create per-environment configs (dev, uat, pre-prod, prod)
4. Generate stacks: VPC, ALB, ECS (per service), CloudFront, WAF, ECR, DNS

<!-- END TEMPLATE -->
