# ECS Fargate — Assess / Inventory

Reverse-engineer an already-deployed module into `design/design.yaml` by reading the
CDK's **intent** and cross-checking it against **live AWS**. Live AWS is authoritative
when the two differ; differences go into a drift report.

## Inputs

| Side | Source | How |
|------|--------|-----|
| **Intended** | the CDK | run `cdk synth` → the resolved CloudFormation template(s) |
| **Reality** | live AWS | AWS CLI/API (e.g. the `call_aws` tool), per account/region |

---

## Step 1 — Identify the app's resources (tags, then naming)

Resources created by this skill's handoff (`coding-cdk-ts`) are tagged. Seed discovery from:

| Tag | Value | Meaning |
|-----|-------|---------|
| `Project` | `{app}` | the module/project name — **primary filter** |
| `Environment` | `dev`\|`sit`\|`uat`\|`pre-prod`\|`prod` | which env |
| `ManagedBy` | `cdk` | CDK-managed; an app resource **without** this (or absent from `cdk synth`) is likely a manual change → drift |
| `Owner`, `Team` | — | metadata → `project` |

- **Primary:** resources where `Project={app}` (and `Environment={env}` for a given env).
- **Fallback:** name prefix `{app}-{env}-*` (for resources that predate tagging).
- A resource counts as the app's if **tag or name** matches.

## Step 2 — Follow dependencies (expand the graph)

Tagged resources are only the **seeds**. Traverse from each to its connected resources —
**including untagged / shared ones** — so the inventory is complete:

```
ECS service ─┬─ task definition ── task role / execution role, log group, ECR repo
             ├─ security group ── ingress/egress peers
             └─ target group ── ALB ── listener(s) ── ACM cert
ALB / ECS SG ── subnets ── VPC ── route tables ── IGW / NAT / TGW attachment ── (VPN/CGW)
CloudFront ── origin (ALB) , WAF WebACL
service ── data services (Aurora/RDS, ElastiCache, S3, SQS, DocumentDB) via SG rules / env / IAM
```

Resources reached **only by traversal** (not tagged with this app) are **shared/external** —
record them as `type: existing` in the yaml and list them in the drift report.

## Step 3 — Detect env / tier and group

- **env** from the `Environment` tag, else the `{env}` in the name.
- **tier** from env: `dev|sit|uat → non-prod`, `pre-prod → pre-prod`, `prod → prod`.
- Group envs that resolve to the same structure for the views (see `SKILL.md` → views per env-group).
- An env that diverges in a few fields → record it with `project.env[].overrides`.

## Step 4 — Map resource → `design.yaml`

| Live AWS resource | `design.yaml` location |
|-------------------|------------------------|
| VPC + subnets (+ IGW / NAT / route tables / TGW) | `networking.tiers.<tier>` — shared → `type: existing` (vpcId + subnet `ids`); owned → `type: create` (reconstruct cidrs / gateways / routes) |
| ALB + listener | `platform.tiers.<tier>.alb` — shared → `type: existing` (albArn + listenerArn); owned → `type: create` (scheme, sslPolicy) |
| ACM certificate | `platform.tiers.<tier>.acm` (`type: existing` arn + domain, or `create-new`) |
| ECS cluster | `platform.tiers.<tier>.ecs` (containerInsights) |
| ECR repository | `platform.tiers.<tier>.ecr` (mutability, shared) |
| ECS service + task def + listener rule | `services[]` (name, type, port, cpu, memory, desiredCount; `path` from the listener rule; `health` from the target group) |
| CloudFront distribution | `platform.tiers.<tier>.cloudfront` |
| WAF WebACL | `platform.tiers.<tier>.waf` (mode, rateLimit) |
| Aurora/RDS, ElastiCache, S3, SQS, DocumentDB | `dataServices.*` |
| tags `Project` / `Owner` / `Team` | `project.name` + metadata |

- **Sizing:** `cpu`/`memory`/`desiredCount` are the **prod baseline**; if non-prod is smaller and matches the derive policy, leave it derived — only write a value when it does NOT match the derive.
- **Per-env exceptions:** if one env in a group differs (e.g. uat has WAF, dev/sit don't) → `project.env[].overrides`.

## Step 5 — Reconcile + drift report

`design/design.yaml` reflects **reality** (live AWS wins). Then write **`design/<group>/drift-report.md`**:

| Section | Contents |
|---------|----------|
| **In CDK, not deployed** | present in `cdk synth`, absent in live AWS |
| **Deployed, not in CDK** | present in live AWS, absent in `cdk synth` (incl. manual changes / missing `ManagedBy=cdk`) |
| **Config differs** | same resource, different settings — table: `field | CDK (synth) | live AWS` |
| **Shared / external** | resources reached by dependency traversal but not owned/tagged by this app |

Close with a short summary: counts per section + whether the design is in sync.
