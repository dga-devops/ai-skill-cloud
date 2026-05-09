# Post-Deploy Asset Sync Reference

Runs after every successful `cdk deploy`. Syncs all deployed AWS resources
to the ClickUp Cloud Assets list as defined in `clickup.md`.

Full field mapping and AWS CLI commands per resource type are in
`asset-cdk-clickup/references/resource-fields.md`.

---

## Sync Procedure

```
1. Collect ARNs
   A. Read outputs.json (from --outputs-file flag) → explicit CfnOutput ARNs
   B. Run: aws cloudformation list-stack-resources --stack-name <StackName>
      → all resources with physical IDs
   Deduplicate by ARN. Source A takes priority.

2. Enrich each resource
   → Call AWS CLI per resource type (see asset-cdk-clickup/references/resource-fields.md)
   → Extract: version, encryption, public_access, security_notes

3. Upsert to ClickUp
   FOR each resource:
     → Search cloud_assets_list by ARN (clickup_search)
     → IF found  → clickup_update_task (version, encryption, public_access, last_deployed)
     → IF not found → clickup_create_task with all fields

4. Report
   Created : N new assets
   Updated : N existing assets
   ⚠️  Flags : list resources with encryption=Disabled or public_access=Public
```

---

## Task Format in ClickUp

**Task name:** `[{{env}}] {{ResourceType}} - {{ResourceName}}`
Example: `[prod] Lambda - api-handler`

**Custom fields to set:**

| Field | Value |
|---|---|
| ARN | full ARN string (primary key — never overwrite on update) |
| Resource Type | Lambda / S3 / RDS / ECS Service / ALB / etc. |
| Stack Name | CDK stack name |
| Environment | sandbox / dev / uat / prod |
| AWS Account | 12-digit account ID |
| AWS Region | e.g. ap-southeast-1 |
| Version | runtime / image tag / engine version |
| Encryption | Enabled / Disabled / N/A |
| Public Access | Public / Private / N/A |
| Last Deployed | YYYY-MM-DD |
| Security Notes | 1-2 line summary of key security observations |

---

## Security Flags

Always flag these in the sync report:

| Condition | Flag |
|---|---|
| `encryption = Disabled` | ⚠️ Encryption disabled |
| `public_access = Public` | ⚠️ Publicly accessible (unless ALB/CloudFront by design) |
| Lambda with no VPC | ⚠️ No VPC isolation |
| RDS `publicly_accessible = true` | ⚠️ RDS exposed to internet |
| S3 with any public access block = false | ⚠️ S3 public access not fully blocked |
