# AWS Resource Naming Limits

Validate all generated resource names against these limits. Use the longest environment name (`pre-prod`) to test.

| Resource | Max Length | Notes |
|----------|-----------|-------|
| Target Group | 32 | Most restrictive — validate first |
| ALB / NLB | 32 | |
| Security Group (Name tag) | 255 | |
| ECS Cluster | 255 | |
| ECS Service | 255 | |
| ECR Repository | 256 | |
| CloudWatch Log Group | 512 | |
| CloudFront Distribution | 255 | Comment field |
| WAF WebACL | 128 | |
| IAM Role | 64 | |
| S3 Bucket | 63 | Must be globally unique |
| Route 53 Record | 255 | |
| Lambda Function | 64 | |
| SQS Queue | 80 | |
| SNS Topic | 256 | |
| DynamoDB Table | 255 | |
| Secrets Manager | 512 | |

## Common Abbreviations

When names exceed limits, use these abbreviations:

| Full | Short |
|------|-------|
| frontend | fe |
| backend | be |
| service | svc |
| database | db |
| production | prod |
| development | dev |
| pre-production | pre-prod |

## Validation Formula

```
length("${projectName}-${longestEnvName}-<resource>-<purpose>") <= limit
```

Example: `emergency-call-pre-prod-tg-frontend` = 36 chars > 32 limit → use `tg-fe` instead.
