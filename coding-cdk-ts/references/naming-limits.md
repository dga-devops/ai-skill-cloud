# AWS Resource Naming Limits

Validate all generated resource names against these limits. Use the longest environment name (`pre-prod`) to test.

## Limits Table

| Resource | Max Length | Notes |
|----------|-----------|-------|
| Target Group | 32 | Most restrictive — validate first |
| ALB / NLB | 32 | |
| IAM Role | 64 | |
| S3 Bucket | 63 | Must be globally unique |
| Lambda Function | 64 | |
| SQS Queue | 80 | |
| WAF WebACL | 128 | |
| SNS Topic | 256 | |
| ECS Cluster | 255 | |
| ECS Service | 255 | |
| ECR Repository | 256 | |
| Security Group (Name tag) | 255 | |
| CloudWatch Log Group | 512 | |
| Secrets Manager | 512 | |
| DynamoDB Table | 255 | |
| Route 53 Record | 255 | |

## Abbreviations

When names exceed limits, shorten the purpose suffix:

| Full | Short |
|------|-------|
| frontend | fe |
| backend | be |
| service | svc |
| database | db |

## Validation

```typescript
// In config, verify before using:
const name = `${projectName}-${envName}-tg-${purpose}`;
if (name.length > 32) throw new Error(`Target Group name "${name}" exceeds 32 char limit`);
```

Test with longest env name: `pre-prod` (8 chars including hyphen in pattern).
