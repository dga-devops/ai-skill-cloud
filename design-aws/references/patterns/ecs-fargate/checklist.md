# ECS Fargate — Pattern Checklist

> **Pattern:** `ecs-fargate`
> **Prerequisite:** Complete `references/shared/checklist-common.md` first.
> **Defaults:** See `defaults.md` in this folder for compute spec calculation and ECS-specific defaults.

---

## Section 1: Networking

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 1.1 | VPC strategy | select | non-prod: `existing`, pre-prod/prod: `dedicated` | always |
| 1.2 | VPC ID (existing) | text | read from `dev-infra.yaml` | when 1.1 = existing |
| 1.3 | Container Subnet IDs (for ECS tasks) | text[] | read from `dev-infra.yaml` | when 1.1 = existing |
| 1.4 | Public Subnet IDs (for ALB) | text[] | read from `dev-infra.yaml` | when 1.1 = existing |
| 1.5 | Private Subnet IDs (optional, for internal resources) | text[] | read from `dev-infra.yaml` | when 1.1 = existing |
| 1.6 | CIDR block | text | `10.0.0.0/16` | when 1.1 = dedicated |
| 1.7 | Number of AZs | select | `2` | when 1.1 = dedicated |
| 1.8 | NAT Gateway strategy | select | pre-prod: `single`, prod: `one-per-az` | when 1.1 = dedicated |

**Non-prod existing resource logic:**
1. Ask: "Do you want to read existing resource IDs from `dev-infra.yaml`?"
2. If yes → read file → use values → ask only for missing fields
3. If no or file not found → ask VPC ID, Subnet IDs directly

---

## Section 2: Compute (ECS) — Multi-Service

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 2.1 | Launch type | select | `fargate` | always |
| 2.2 | Number of services | number | `1` | always |

**Per-service questions (repeat for each service):**

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 2.3 | Service name | text | `api` | per service |
| 2.4 | Service type | select | `api` / `frontend` / `worker` | per service |
| 2.5 | Container port | number | api: `3000`, frontend: `4200` | per service |
| 2.6 | CPU (prod) | select | from intake | per service |
| 2.7 | Memory MB (prod) | select | from intake | per service |
| 2.8 | CPU (non-prod) | auto | prod / 2 (min 256) | per service |
| 2.9 | Memory MB (non-prod) | auto | prod / 2 (min 512) | per service |
| 2.10 | Desired count (prod) | number | `2` | per service |
| 2.11 | Desired count (non-prod) | number | `1` | per service |
| 2.12 | Min tasks | number | `1` | per service |
| 2.13 | Max tasks (prod) | number | `4` | per service |
| 2.14 | Scaling metric | select | `cpu` | per service |
| 2.15 | Scaling target (%) | number | `70` | per service |
| 2.16 | Health check path | text | `/health` | per service |
| 2.17 | Enable execute command | boolean | non-prod: `true`, pre-prod/prod: `false` | per service |

**Service types:**
- `api` — backend API service (routed via ALB, no CF cache)
- `frontend` — frontend/SSR service (routed via ALB, CF cached)
- `worker` — background worker (no ALB target, no CF behavior)

---

## Section 3: Load Balancer (ALB) — Path-Based Routing

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 3.1 | ALB strategy | select | non-prod: `existing`, pre-prod/prod: `dedicated` | always |
| 3.2 | ALB ARN (existing) | text | read from `dev-infra.yaml` | when 3.1 = existing |
| 3.3 | Listener ARN (existing) | text | read from `dev-infra.yaml` | when 3.1 = existing |
| 3.4 | Scheme | select | `internet-facing` | when 3.1 = dedicated |
| 3.5 | SSL certificate | select | `create-new` | when 3.1 = dedicated |
| 3.6 | Base path prefix | text | `/cp/dga/{app-name}` | always |
| 3.7 | Health check interval (s) | number | `30` | always |
| 3.8 | Healthy threshold | number | `3` | always |
| 3.9 | Unhealthy threshold | number | `3` | always |

**Per-service path routing (non-worker services only):**

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 3.10 | Path pattern | text | api: `{base}/api/*`, frontend: `{base}/*` | per service |
| 3.11 | Priority | number | api: `1` (higher), frontend: `2` (lower/default) | per service |

---

## Section 4: CDN and Security (CloudFront + WAF)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 4.1 | CloudFront enabled | boolean | `true` | always |
| 4.2 | Origin protocol policy | select | `https-only` | when 4.1 = true |
| 4.3 | WAF enabled | boolean | non-prod: `false`, pre-prod/prod: `true` | when 4.1 = true |
| 4.4 | WAF rule sets | multi-select | `[AWSManagedRulesCommonRuleSet, AWSManagedRulesKnownBadInputsRuleSet]` | when 4.3 = true |
| 4.5 | Rate limit (req/5min) | number | `2000` | when 4.3 = true |

**Per-service CloudFront behaviors (non-worker services only):**

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 4.6 | Path pattern | text | same as ALB path (Section 3.10) | per service |
| 4.7 | Cache policy | select | frontend: `caching-optimized`, api: `caching-disabled` | per service |
| 4.8 | Priority | number | api behaviors first, frontend as default | per service |

---

## Section 5: Database (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 5.1 | Database enabled | boolean | `false` | always |
| 5.2 | Database type | select | `aurora-postgresql` | when 5.1 = true |
| 5.3 | Engine version | text | `15.4` | when 5.2 = aurora-* |
| 5.4 | Database name | text | `appdb` | when 5.2 = aurora-* |
| 5.5 | Instance class | select | `db.t4g.medium` | when 5.2 = aurora-* |
| 5.6 | Serverless v2 min ACU | number | `0.5` | when 5.2 = aurora-* |
| 5.7 | Serverless v2 max ACU | number | non-prod: `2`, prod: `8` | when 5.2 = aurora-* |
| 5.8 | Multi-AZ (reader) | boolean | non-prod/pre-prod: `false`, prod: `true` | when 5.2 = aurora-* |
| 5.9 | Backup retention (days) | number | non-prod: `7`, pre-prod: `14`, prod: `30` | when 5.2 = aurora-* |
| 5.10 | Deletion protection | boolean | non-prod: `false`, pre-prod/prod: `true` | when 5.2 = aurora-* |
| 5.11 | DynamoDB billing mode | select | `PAY_PER_REQUEST` | when 5.2 = dynamodb |
| 5.12 | DynamoDB table name | text | — | when 5.2 = dynamodb |
| 5.13 | Partition key (name:type) | text | — | when 5.2 = dynamodb |
| 5.14 | Sort key (name:type) | text | — | when 5.2 = dynamodb |

---

## Section 6: Storage (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 6.1 | S3 storage enabled | boolean | `false` | always |
| 6.2 | Bucket purpose | text | — | when 6.1 = true |
| 6.3 | Versioning | boolean | `true` | when 6.1 = true |
| 6.4 | Lifecycle (days, 0=never) | number | `90` | when 6.1 = true |
| 6.5 | Encryption | select | `AES256` | when 6.1 = true |
| 6.6 | Public access | boolean | `false` | when 6.1 = true |
| 6.7 | Additional buckets? | boolean | `false` | when 6.1 = true |

---

## Section 7: Queue/Messaging (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 7.1 | Queue enabled | boolean | `false` | always |
| 7.2 | Queue type | select | `sqs` | when 7.1 = true |
| 7.3 | Queue name/purpose | text | — | when 7.1 = true |
| 7.4 | Visibility timeout (s) | number | `30` | when 7.2 = sqs/sqs-fifo |
| 7.5 | Dead letter queue | boolean | `true` | when 7.2 = sqs/sqs-fifo |
| 7.6 | Max receive count | number | `3` | when 7.5 = true |
| 7.7 | EventBridge enabled | boolean | `false` | when 7.1 = true |
| 7.8 | Event bus name | text | `default` | when 7.7 = true |
| 7.9 | Event rules/patterns | text[] | — | when 7.7 = true |

---

## Section 8: Cache (optional)

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 8.1 | Cache enabled | boolean | `false` | always |
| 8.2 | Cache type | select | `redis` | when 8.1 = true |
| 8.3 | Node type | select | `cache.t4g.micro` | when 8.1 = true |
| 8.4 | Number of nodes | number | non-prod: `1`, prod: `2` | when 8.1 = true |
| 8.5 | Cluster mode | boolean | `false` | when 8.2 = redis |
| 8.6 | Engine version | text | `7.0` | when 8.1 = true |
