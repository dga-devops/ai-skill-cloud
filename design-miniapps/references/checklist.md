# Design Checklist — Miniapps

Complete list of questions to collect architecture requirements for a new miniapp.

---

## Section 1: App Identity

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 1.1 | App name (projectName) | text | — | always |
| 1.2 | Short description | text | — | always |
| 1.3 | Owner | text | — | always |
| 1.4 | Team tag | text | — | always |
| 1.5 | Environments required | multi-select | `[dev, uat, pre-prod, prod]` | always |
| 1.6 | Account ID per environment | text per env | — | always |
| 1.7 | Region | select | `ap-southeast-1` | always |

---

## Section 2: Networking

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 2.1 | VPC strategy | select | non-prod: `existing`, pre-prod/prod: `dedicated` | always |
| 2.2 | VPC ID (existing) | text | read from `dev-infra.yaml` | when 2.1 = existing |
| 2.3 | Container Subnet IDs (for ECS tasks) | text[] | read from `dev-infra.yaml` | when 2.1 = existing |
| 2.4 | Public Subnet IDs (for ALB) | text[] | read from `dev-infra.yaml` | when 2.1 = existing |
| 2.5 | Private Subnet IDs (optional, for internal resources) | text[] | read from `dev-infra.yaml` | when 2.1 = existing |
| 2.5 | CIDR block | text | `10.0.0.0/16` | when 2.1 = dedicated |
| 2.6 | Number of AZs | select | `2` | when 2.1 = dedicated |
| 2.7 | NAT Gateway strategy | select | pre-prod: `single`, prod: `one-per-az` | when 2.1 = dedicated |

**Non-prod existing resource logic:**
1. Ask: "Do you want to read existing resource IDs from `dev-infra.yaml`?"
2. If yes -> read file -> use values -> ask only for missing fields
3. If no or file not found -> ask VPC ID, Subnet IDs directly

---

## Section 3: Compute (ECS) — Multi-Service

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 3.1 | Launch type | select | `fargate` | always |
| 3.2 | Number of services | number | `1` | always |

**Per-service questions (repeat for each service):**

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 3.3 | Service name | text | `api` | per service |
| 3.4 | Service type | select | `api` / `frontend` / `worker` | per service |
| 3.5 | Container port | number | api: `3000`, frontend: `4200` | per service |
| 3.6 | CPU (prod) | select | from intake | per service |
| 3.7 | Memory MB (prod) | select | from intake | per service |
| 3.8 | CPU (non-prod) | auto | prod / 2 (min 256) | per service |
| 3.9 | Memory MB (non-prod) | auto | prod / 2 (min 512) | per service |
| 3.10 | Desired count (prod) | number | `2` | per service |
| 3.11 | Desired count (non-prod) | number | `1` | per service |
| 3.12 | Min tasks | number | `1` | per service |
| 3.13 | Max tasks (prod) | number | `4` | per service |
| 3.14 | Scaling metric | select | `cpu` | per service |
| 3.15 | Scaling target (%) | number | `70` | per service |
| 3.16 | Health check path | text | `/health` | per service |
| 3.17 | Enable execute command | boolean | non-prod: `true`, pre-prod/prod: `false` | per service |

**Service types:**
- `api` — backend API service (routed via ALB, no CF cache)
- `frontend` — frontend/SSR service (routed via ALB, CF cached)
- `worker` — background worker (no ALB target, no CF behavior)

---

## Section 4: Load Balancer (ALB) — Path-Based Routing

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 4.1 | ALB strategy | select | non-prod: `existing`, pre-prod/prod: `dedicated` | always |
| 4.2 | ALB ARN (existing) | text | read from `dev-infra.yaml` | when 4.1 = existing |
| 4.3 | Listener ARN (existing) | text | read from `dev-infra.yaml` | when 4.1 = existing |
| 4.4 | Scheme | select | `internet-facing` | when 4.1 = dedicated |
| 4.5 | SSL certificate | select | `create-new` | when 4.1 = dedicated |
| 4.6 | Base path prefix | text | `/cp/dga/{app-name}` | always |
| 4.7 | Health check interval (s) | number | `30` | always |
| 4.8 | Healthy threshold | number | `3` | always |
| 4.9 | Unhealthy threshold | number | `3` | always |

**Per-service path routing (non-worker services only):**

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 4.10 | Path pattern | text | api: `{base}/api/*`, frontend: `{base}/*` | per service |
| 4.11 | Priority | number | api: `1` (higher), frontend: `2` (lower/default) | per service |

---

## Section 5: CDN and Security (CloudFront + WAF) — Multiple Behaviors

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 5.1 | CloudFront enabled | boolean | `true` | always |
| 5.2 | Origin protocol policy | select | `https-only` | when 5.1 = true |
| 5.3 | WAF enabled | boolean | non-prod: `false`, pre-prod/prod: `true` | when 5.1 = true |
| 5.4 | WAF rule sets | multi-select | `[AWSManagedRulesCommonRuleSet, AWSManagedRulesKnownBadInputsRuleSet]` | when 5.3 = true |
| 5.5 | Rate limit (req/5min) | number | `2000` | when 5.3 = true |

**Per-service CloudFront behaviors (non-worker services only):**

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 5.6 | Path pattern | text | same as ALB path (Section 4.10) | per service |
| 5.7 | Cache policy | select | frontend: `caching-optimized`, api: `caching-disabled` | per service |
| 5.8 | Priority | number | api behaviors first, frontend as default | per service |

---

## Section 6: Database (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 6.1 | Database enabled | boolean | `false` | always |
| 6.2 | Database type | select | `aurora-postgresql` | when 6.1 = true |
| 6.3 | Engine version | text | `15.4` | when 6.2 = aurora-* |
| 6.4 | Database name | text | `appdb` | when 6.2 = aurora-* |
| 6.5 | Instance class | select | `db.t4g.medium` | when 6.2 = aurora-* |
| 6.6 | Serverless v2 min ACU | number | `0.5` | when 6.2 = aurora-* |
| 6.7 | Serverless v2 max ACU | number | non-prod: `2`, prod: `8` | when 6.2 = aurora-* |
| 6.8 | Multi-AZ (reader) | boolean | non-prod/pre-prod: `false`, prod: `true` | when 6.2 = aurora-* |
| 6.9 | Backup retention (days) | number | non-prod: `7`, pre-prod: `14`, prod: `30` | when 6.2 = aurora-* |
| 6.10 | Deletion protection | boolean | non-prod: `false`, pre-prod/prod: `true` | when 6.2 = aurora-* |
| 6.11 | DynamoDB billing mode | select | `PAY_PER_REQUEST` | when 6.2 = dynamodb |
| 6.12 | DynamoDB table name | text | — | when 6.2 = dynamodb |
| 6.13 | Partition key (name:type) | text | — | when 6.2 = dynamodb |
| 6.14 | Sort key (name:type) | text | — | when 6.2 = dynamodb |

---

## Section 7: Storage (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 7.1 | S3 storage enabled | boolean | `false` | always |
| 7.2 | Bucket purpose | text | — | when 7.1 = true |
| 7.3 | Versioning | boolean | `true` | when 7.1 = true |
| 7.4 | Lifecycle (days, 0=never) | number | `90` | when 7.1 = true |
| 7.5 | Encryption | select | `AES256` | when 7.1 = true |
| 7.6 | Public access | boolean | `false` | when 7.1 = true |
| 7.7 | Additional buckets? | boolean | `false` | when 7.1 = true |

---

## Section 8: Queue/Messaging (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 8.1 | Queue enabled | boolean | `false` | always |
| 8.2 | Queue type | select | `sqs` | when 8.1 = true |
| 8.3 | Queue name/purpose | text | — | when 8.1 = true |
| 8.4 | Visibility timeout (s) | number | `30` | when 8.2 = sqs/sqs-fifo |
| 8.5 | Dead letter queue | boolean | `true` | when 8.2 = sqs/sqs-fifo |
| 8.6 | Max receive count | number | `3` | when 8.5 = true |
| 8.7 | EventBridge enabled | boolean | `false` | when 8.1 = true |
| 8.8 | Event bus name | text | `default` | when 8.7 = true |
| 8.9 | Event rules/patterns | text[] | — | when 8.7 = true |

---

## Section 9: Cache (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 9.1 | Cache enabled | boolean | `false` | always |
| 9.2 | Cache type | select | `redis` | when 9.1 = true |
| 9.3 | Node type | select | `cache.t4g.micro` | when 9.1 = true |
| 9.4 | Number of nodes | number | non-prod: `1`, prod: `2` | when 9.1 = true |
| 9.5 | Cluster mode | boolean | `false` | when 9.2 = redis |
| 9.6 | Engine version | text | `7.0` | when 9.1 = true |

---

## Section 10: DNS and Certificates — Domain Per Environment

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 10.1 | Domain strategy | select | `per-env` | always |
| 10.2 | Non-prod base domain | text | — | always |
| 10.3 | Non-prod domain pattern | text | `{app}-{env}.{base-domain}` | always |
| 10.4 | Prod base domain | text | — | always |
| 10.5 | Prod domain pattern | text | `{app}.{base-domain}` | always |
| 10.6 | Pre-prod domain pattern | text | `{app}-pre-prod.{prod-base-domain}` | when pre-prod exists |
| 10.7 | Route53 hosted zone strategy | select | `existing` | always |
| 10.8 | Hosted zone ID (non-prod domain) | text | — | when 10.7 = existing |
| 10.9 | Hosted zone ID (prod domain) | text | — | when 10.7 = existing |
| 10.10 | ACM certificate strategy | select | `create-new` | always |

**Example output:**
```
dev:      {app}-dev.{non-prod-base}
uat:      {app}-uat.{non-prod-base}
pre-prod: {app}-pre-prod.{prod-base}
prod:     {app}.{prod-base}
```

---

## Section 11: Observability

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 11.1 | Log retention (days) | select | non-prod: `14`, pre-prod: `30`, prod: `90` | always |
| 11.2 | CPU alarm threshold (%) | number | `80` | always |
| 11.3 | Memory alarm threshold (%) | number | `80` | always |
| 11.4 | Error rate threshold (%) | number | `5` | always |
| 11.5 | X-Ray tracing | boolean | `false` | always |
| 11.6 | CloudWatch dashboard | boolean | non-prod: `false`, pre-prod/prod: `true` | always |

---

## Section 12: Security and IAM

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 12.1 | Secrets (Secrets Manager) | text[] | — | always |
| 12.2 | IAM permissions needed (task role) | text[] | — (TBD if unknown) | always |
| 12.3 | Egress rules | select | `all-outbound` | always |
| 12.4 | cdk-nag enabled | boolean | dev: `false`, uat/pre-prod/prod: `true` | always |

**Auto-derived (do NOT ask user — generate from services):**

- **sg-alb**: Inbound TCP 443 from 0.0.0.0/0; Outbound TCP {each service port} to sg-ecs
- **sg-ecs**: Inbound TCP {each service port} from sg-alb; Outbound TCP 443 to 0.0.0.0/0
- **Execution Role**: ECR pull + CloudWatch Logs + Secrets (if 12.1 is not empty)
- **Task Role**: from 12.2 (or TBD if unknown)

---

## Section 13: CI/CD and ECR

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 13.1 | ECR removal policy | select | non-prod: `destroy`, pre-prod/prod: `retain` | always |
| 13.2 | Image tag strategy | select | `git-sha` | always |
| 13.3 | Deploy strategy | select | `rolling` | always |
| 13.4 | Max image count | number | non-prod: `5`, prod: `30` | always |

**Note:** ECR repository created per service: `{app-name}-{service-name}`.
