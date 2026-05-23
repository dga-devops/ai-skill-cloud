# Common Design Checklist

Shared sections applicable to all architecture patterns. Complete these before pattern-specific sections.

---

## Section 1: App Identity

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 1.1 | App name (projectName) | text | — | always |
| 1.2 | Short description | text | — | always |
| 1.3 | Owner | text | — | always |
| 1.4 | Team tag | text | — | always |
| 1.5 | Architecture pattern | select | — | always (from pattern registry) |
| 1.6 | Environments required | multi-select | `[dev, uat, pre-prod, prod]` | always |
| 1.7 | Account ID per environment | text per env | — | always |
| 1.8 | Region | select | `ap-southeast-1` | always |

---

## Section 2: DNS and Certificates

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 2.1 | Domain strategy | select | `per-env` | always |
| 2.2 | Non-prod base domain | text | — | always |
| 2.3 | Non-prod domain pattern | text | `{app}-{env}.{base-domain}` | always |
| 2.4 | Prod base domain | text | — | always |
| 2.5 | Prod domain pattern | text | `{app}.{base-domain}` | always |
| 2.6 | Pre-prod domain pattern | text | `{app}-pre-prod.{prod-base-domain}` | when pre-prod exists |
| 2.7 | Route53 hosted zone strategy | select | `existing` | always |
| 2.8 | Hosted zone ID (non-prod domain) | text | — | when 2.7 = existing |
| 2.9 | Hosted zone ID (prod domain) | text | — | when 2.7 = existing |
| 2.10 | ACM certificate strategy | select | `create-new` | always |

**Example output:**
```
dev:      {app}-dev.{non-prod-base}
uat:      {app}-uat.{non-prod-base}
pre-prod: {app}-pre-prod.{prod-base}
prod:     {app}.{prod-base}
```

---

## Section 3: Observability

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 3.1 | Log retention (days) | select | non-prod: `14`, pre-prod: `30`, prod: `90` | always |
| 3.2 | CPU alarm threshold (%) | number | `80` | always |
| 3.3 | Memory alarm threshold (%) | number | `80` | always |
| 3.4 | Error rate threshold (%) | number | `5` | always |
| 3.5 | X-Ray tracing | boolean | `false` | always |
| 3.6 | CloudWatch dashboard | boolean | non-prod: `false`, pre-prod/prod: `true` | always |

---

## Section 4: Security and IAM

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 4.1 | Secrets (Secrets Manager) | text[] | — | always |
| 4.2 | IAM permissions needed (task role) | text[] | — (TBD if unknown) | always |
| 4.3 | Egress rules | select | `all-outbound` | always |
| 4.4 | cdk-nag enabled | boolean | dev: `false`, uat/pre-prod/prod: `true` | always |

**Auto-derived (do NOT ask user — generate from pattern):**

- Security Group rules — derived from pattern's service/port definitions
- Execution Role — derived from pattern's compute type (e.g., ECR pull + CW Logs for containers)
- Task Role — from 4.2 (or TBD if unknown)

---

## Section 5: CI/CD and Container Registry

| # | Question | Type | Default | Condition |
|---|----------|------|---------|-----------|
| 5.1 | Registry removal policy | select | non-prod: `destroy`, pre-prod/prod: `retain` | when pattern uses containers |
| 5.2 | Image tag strategy | select | `git-sha` | when pattern uses containers |
| 5.3 | Deploy strategy | select | `rolling` | always |
| 5.4 | Max image count | number | non-prod: `5`, prod: `30` | when pattern uses containers |

**Note:** Container registry created per service: `{app-name}-{service-name}`.
