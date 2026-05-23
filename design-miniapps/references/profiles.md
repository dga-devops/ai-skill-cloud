# Profiles — Environment Tier Defaults

Defaults are determined by environment tier, not size. User provides prod spec; non-prod is auto-calculated.

---

## Environment Tiers

### non-prod (dev, uat)

Uses shared/existing resources to reduce cost. Spec = prod / 2.

| Field | Value |
|-------|-------|
| VPC | existing (shared) |
| ALB | existing (shared) |
| CloudFront | enabled |
| WAF | disabled |
| NAT Gateway | single (if dedicated VPC) |
| Multi-AZ | false |
| Deletion protection | false |
| cdk-nag | dev: disabled, uat: enabled |
| ECR removal policy | destroy |
| Execute command | true |
| Log retention | 14 days |
| Backup retention | 7 days |
| CloudWatch dashboard | false |
| Deploy strategy | rolling |
| CPU | prod / 2 (min 256) |
| Memory | prod / 2 (min 512) |
| Desired count | 1 |
| Max tasks | 2 |

### pre-prod

Dedicated resources, WAF enabled, but no HA. Spec = same as prod.

| Field | Value |
|-------|-------|
| VPC | dedicated |
| ALB | dedicated |
| CloudFront | enabled |
| WAF | enabled |
| NAT Gateway | single |
| Multi-AZ | false |
| Deletion protection | true |
| cdk-nag | enabled |
| ECR removal policy | retain |
| Execute command | false |
| Log retention | 30 days |
| Backup retention | 14 days |
| CloudWatch dashboard | true |
| Deploy strategy | rolling |
| CPU | same as prod |
| Memory | same as prod |
| Desired count | 1 |
| Max tasks | 2 |

### prod

Dedicated resources, full security, high availability.

| Field | Value |
|-------|-------|
| VPC | dedicated |
| ALB | dedicated |
| CloudFront | enabled |
| WAF | enabled |
| NAT Gateway | one-per-az |
| Multi-AZ | true |
| Deletion protection | true |
| cdk-nag | enabled |
| ECR removal policy | retain |
| Execute command | false |
| Log retention | 90 days |
| Backup retention | 30 days |
| CloudWatch dashboard | true |
| Deploy strategy | rolling |
| CPU | as specified |
| Memory | as specified |
| Desired count | 2+ |
| Max tasks | 4+ |

---

## Spec Calculation

User provides **prod spec** per service. Other tiers are derived:

```
Input:  prod CPU = 2048, prod Memory = 4096

Output:
  prod:     CPU 2048, Memory 4096, desired 2, max 4
  pre-prod: CPU 2048, Memory 4096, desired 1, max 2
  non-prod: CPU 1024, Memory 2048, desired 1, max 2
```

Formula:
- `non-prod CPU = max(256, prod CPU / 2)`
- `non-prod Memory = max(512, prod Memory / 2)`
- `pre-prod CPU = prod CPU`
- `pre-prod Memory = prod Memory`

---

## Domain Pattern

Domains are split by base domain per tier:

```
non-prod: {app}-{env}.{non-prod-base-domain}
pre-prod: {app}-pre-prod.{prod-base-domain}
prod:     {app}.{prod-base-domain}
```

Example:
```
dev:      my-app-dev.nonprod-domain.example
uat:      my-app-uat.nonprod-domain.example
pre-prod: my-app-pre-prod.prod-domain.example
prod:     my-app.prod-domain.example
```

---

## Quick Mode Workflow

In Quick mode, present tier defaults per section and ask user to confirm:

1. Ask prod spec (CPU, Memory per service)
2. Auto-calculate non-prod and pre-prod
3. Present all values grouped by section
4. User confirms or overrides specific fields
