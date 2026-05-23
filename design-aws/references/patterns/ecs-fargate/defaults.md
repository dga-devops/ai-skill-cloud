# ECS Fargate — Pattern Defaults

> **Pattern:** `ecs-fargate`
> Compute-specific defaults and spec calculation for ECS Fargate.

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

## Compute Defaults Per Tier

| Field | non-prod | pre-prod | prod |
|-------|----------|----------|------|
| CPU | prod / 2 (min 256) | same as prod | as specified |
| Memory | prod / 2 (min 512) | same as prod | as specified |
| Desired count | 1 | 1 | 2+ |
| Max tasks | 2 | 2 | 4+ |
| Min tasks | 1 | 1 | 1 |
| Scaling metric | cpu | cpu | cpu |
| Scaling target | 70% | 70% | 70% |
| Execute command | true | false | false |
| ECR removal policy | destroy | retain | retain |

---

## Service Type Defaults

| Service Type | Port | ALB Path | CF Cache Policy | ALB Target |
|-------------|------|----------|-----------------|------------|
| `api` | 3000 | `{base}/api/*` | caching-disabled | yes |
| `frontend` | 4200 | `{base}/*` | caching-optimized | yes |
| `worker` | — | — | — | no |

---

## CloudFront Behavior Priority

1. API services first (specific paths, higher priority)
2. Frontend services as default/catch-all (lower priority)
3. Workers have no CF behavior

---

## Quick Mode Flow

1. Ask: number of services + name/type per service
2. Ask: prod CPU and Memory per service
3. Auto-calculate all tiers using formulas above
4. Present computed values → user confirms or overrides
