# AWS Resource Fields Reference

For each resource type, this document defines:
- AWS CLI command to enrich details
- Fields to extract → ClickUp field mapping

---

## Common Fields (all resource types)

Extracted from `aws cloudformation list-stack-resources`:

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `PhysicalResourceId` | ARN | May be ARN or name — construct ARN if needed |
| `ResourceType` | Resource Type | e.g. `AWS::Lambda::Function` → `Lambda` |
| Stack name (from CLI arg) | Stack Name | |
| Detected from stack name suffix | Environment | `*-prod`, `*-uat`, `*-dev`, `*-sandbox` |

---

## Lambda (`AWS::Lambda::Function`)

```bash
aws lambda get-function-configuration --function-name <ARN>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `FunctionArn` | ARN | |
| `Runtime` | Version | e.g. `python3.12`, `nodejs20.x` |
| `KMSKeyArn` | Encryption | `Enabled` if set, else `Disabled` |
| `VpcConfig.VpcId` | Security Notes | "VPC: {{vpc_id}}" or "No VPC" |
| `MemorySize` | Security Notes | Append "Memory: {{N}}MB" |
| `Timeout` | Security Notes | Append "Timeout: {{N}}s" |
| `Environment.Variables` | Security Notes | Flag if count > 0 (env vars may contain secrets) |

Public Access: always `Private` (Lambda is not publicly accessible by default).

---

## S3 Bucket (`AWS::S3::Bucket`)

```bash
aws s3api get-bucket-encryption --bucket <name>
aws s3api get-bucket-versioning --bucket <name>
aws s3api get-public-access-block --bucket <name>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| Bucket name | ARN | Construct: `arn:aws:s3:::<name>` |
| `ServerSideEncryptionConfiguration` | Encryption | `Enabled` if rule exists, else `Disabled` |
| `Status` (versioning) | Version | `Versioning: Enabled/Suspended/Disabled` |
| `BlockPublicAcls` + `BlockPublicPolicy` | Public Access | `Private` if all 4 flags true, else `Public` |
| `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets` | Security Notes | List any flag that is `false` |

---

## RDS / Aurora (`AWS::RDS::DBInstance`, `AWS::RDS::DBCluster`)

```bash
aws rds describe-db-instances --db-instance-identifier <id>
# or for cluster:
aws rds describe-db-clusters --db-cluster-identifier <id>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `DBInstanceArn` / `DBClusterArn` | ARN | |
| `EngineVersion` | Version | e.g. `aurora-mysql:8.0.28` |
| `StorageEncrypted` | Encryption | `Enabled` / `Disabled` |
| `PubliclyAccessible` | Public Access | `Public` / `Private` |
| `MultiAZ` | Security Notes | "MultiAZ: Yes/No" |
| `DeletionProtection` | Security Notes | Flag if `false` |
| `BackupRetentionPeriod` | Security Notes | Append "Backup: {{N}} days" |

---

## ECS Service (`AWS::ECS::Service`)

```bash
aws ecs describe-services --cluster <cluster> --services <service-arn>
aws ecs describe-task-definition --task-definition <family:revision>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `serviceArn` | ARN | |
| Container image URI + tag | Version | e.g. `123456789.dkr.ecr.../app:v1.2.3` |
| `networkConfiguration.awsvpcConfiguration.assignPublicIp` | Public Access | `Public` if `ENABLED`, else `Private` |
| `cpu` / `memory` (task def) | Security Notes | "CPU: {{N}}, Memory: {{N}}MB" |
| Secrets in task definition | Security Notes | Flag if secrets manager or SSM references exist |

---

## Application Load Balancer (`AWS::ElasticLoadBalancingV2::LoadBalancer`)

```bash
aws elbv2 describe-load-balancers --load-balancer-arns <arn>
aws elbv2 describe-listeners --load-balancer-arn <arn>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `LoadBalancerArn` | ARN | |
| Listener with HTTPS port 443 | Version | SSL policy name, e.g. `ELBSecurityPolicy-TLS13-1-2-2021-06` |
| `Scheme` | Public Access | `internet-facing` → `Public`, `internal` → `Private` |
| HTTPS listener exists? | Encryption | `Enabled` if 443 listener found, else `Disabled` |
| HTTP listener exists? | Security Notes | Flag "HTTP (port 80) listener — consider redirect to HTTPS" |

---

## DynamoDB (`AWS::DynamoDB::Table`)

```bash
aws dynamodb describe-table --table-name <name>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `TableArn` | ARN | |
| `TableStatus` | Version | Include `BillingMode` e.g. `PAY_PER_REQUEST` |
| `SSEDescription.Status` | Encryption | `Enabled` / `Disabled` |
| Public Access | always `Private` | DynamoDB is never publicly accessible |
| `DeletionProtectionEnabled` | Security Notes | Flag if `false` |
| `PointInTimeRecoveryDescription.PointInTimeRecoveryStatus` | Security Notes | "PITR: Enabled/Disabled" |

---

## API Gateway (`AWS::ApiGateway::RestApi`, `AWS::ApiGatewayV2::Api`)

```bash
aws apigateway get-rest-api --rest-api-id <id>
aws apigateway get-stages --rest-api-id <id>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| ARN (constructed) | ARN | `arn:aws:apigateway:<region>::/restapis/<id>` |
| Stage name + deployed date | Version | e.g. `prod (deployed 2026-05-01)` |
| `endpointConfiguration.types` | Public Access | `PRIVATE` → `Private`, else `Public` |
| Stage `defaultRouteSettings.throttlingBurstLimit` | Security Notes | Append "Throttling: {{N}} burst" |
| Authorization type on methods | Security Notes | Flag methods with `NONE` auth |

---

## KMS Key (`AWS::KMS::Key`)

```bash
aws kms describe-key --key-id <key-id>
aws kms get-key-rotation-status --key-id <key-id>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `KeyMetadata.Arn` | ARN | |
| `KeyMetadata.KeySpec` | Version | e.g. `SYMMETRIC_DEFAULT`, `RSA_2048` |
| Always `Enabled` | Encryption | KMS key itself is the encryption mechanism |
| Public Access | always `Private` | |
| `KeyRotationEnabled` | Security Notes | Flag if `false` — "Key rotation: Disabled" |
| `KeyMetadata.KeyState` | Security Notes | Flag if not `Enabled` |

---

## IAM Role (`AWS::IAM::Role`)

```bash
aws iam get-role --role-name <name>
aws iam list-attached-role-policies --role-name <name>
```

| Source Field | ClickUp Field | Notes |
|---|---|---|
| `Role.Arn` | ARN | |
| Attached policy names | Version | List policy names |
| Public Access | always `Private` | |
| Encryption | always `N/A` | |
| `AssumeRolePolicyDocument.Statement[*].Principal` | Security Notes | Flag if Principal is `"*"` (wildcard) |
| `PermissionsBoundary` | Security Notes | "Boundary: set" or "Boundary: NOT SET" |

---

## Resource Type Dropdown Values

Use these exact strings for the `Resource Type` custom field in ClickUp:

```
Lambda
S3
RDS
Aurora
ECS Service
ALB
DynamoDB
API Gateway
KMS Key
IAM Role
CloudFront
SNS Topic
SQS Queue
VPC
EC2 Instance
Other
```
