# Profiles — Environment Tier Defaults

Defaults are determined by environment tier, not size. Pattern-specific compute defaults are in `patterns/<pattern>/defaults.md`.

---

## Environment Tiers

### non-prod (dev, uat)

Uses shared/existing resources to reduce cost.

| Field | Value |
|-------|-------|
| VPC | existing (shared) |
| ALB | existing (shared) |
| WAF | disabled |
| NAT Gateway | single (if dedicated VPC) |
| Multi-AZ | false |
| Deletion protection | false |
| cdk-nag | dev: disabled, uat: enabled |
| Log retention | 14 days |
| Backup retention | 7 days |
| CloudWatch dashboard | false |
| Deploy strategy | rolling |

### pre-prod

Dedicated resources, WAF enabled, but no HA.

| Field | Value |
|-------|-------|
| VPC | dedicated |
| ALB | dedicated |
| WAF | enabled |
| NAT Gateway | single |
| Multi-AZ | false |
| Deletion protection | true |
| cdk-nag | enabled |
| Log retention | 30 days |
| Backup retention | 14 days |
| CloudWatch dashboard | true |
| Deploy strategy | rolling |

### prod

Dedicated resources, full security, high availability.

| Field | Value |
|-------|-------|
| VPC | dedicated |
| ALB | dedicated |
| WAF | enabled |
| NAT Gateway | one-per-az |
| Multi-AZ | true |
| Deletion protection | true |
| cdk-nag | enabled |
| Log retention | 90 days |
| Backup retention | 30 days |
| CloudWatch dashboard | true |
| Deploy strategy | rolling |

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

1. Ask pattern-specific prod spec (e.g., CPU/Memory for containers, memory size for Lambda)
2. Auto-calculate non-prod and pre-prod from pattern defaults
3. Present all values grouped by section
4. User confirms or overrides specific fields
