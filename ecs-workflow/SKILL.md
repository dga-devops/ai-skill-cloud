---
name: ecs-workflow
description: Generate GitHub Actions workflow YAML for deploying to AWS ECS. Use this skill when the user wants to create or update an ECS deployment workflow, configure ECR/ECS settings, change environment variables like AWS_REGION, ECR_REPOSITORY, ECS_SERVICE, ECS_CLUSTER, CONTAINER_NAME, SECRETSMANAGER_ARN, or AWS_ROLE_ARN in a deployment pipeline. Also triggers when the user mentions GitHub Actions + ECS, deploy to ECS, or wants a new workflow YAML for a different project/environment.
---

# ECS Workflow Generator (v2)

สร้างไฟล์ GitHub Actions workflow YAML สำหรับ deploy ไปยัง AWS ECS โดยเขียนขึ้นมาเองทั้งหมดตามกฎด้านล่าง

## ข้อมูลที่ต้องการจาก User

### ต้องถามเสมอ (ห้าม derive เอง)
- `project_name` — ชื่อโปรเจค
- `environment` — uat, prod, dev
- `ecs_cluster` — ชื่อ ECS cluster (อาจไม่ตรงกับชื่อ service)
- `aws_role_arn` — ARN เต็มของ IAM role สำหรับ OIDC
- `secretsmanager_arn` — ARN เต็มของ secret

### Derive ได้ (ถ้า user ไม่ระบุ)
- `aws_region` → default: `ap-southeast-7`
- `ecr_repository` → `{project_name}-{environment}`
- `ecs_service` → `{project_name}-{environment}`
- `container_name` → `{project_name}`
- `tag_pattern` → `{environment}-v.*` แต่ถ้าเป็น prod จะเป็น `v.*`
- `dockerfile_path` → ค้นหาจากโครงสร้าง project ถ้าไม่เจอให้ถาม
- `docker_context` → directory ที่ Dockerfile อยู่

## Workflow Structure

### Triggers
- **push tags**: trigger เมื่อ push tag ที่ match pattern (เช่น `uat-v.*`)
- **workflow_dispatch**: manual trigger พร้อม input `tag` (string) และ `use_secrets_manager` (boolean, default true)

### Environment Variables (global)
ประกาศที่ระดับ `env:` ของ workflow:
- AWS_REGION, ECR_REPOSITORY, ECS_SERVICE, ECS_CLUSTER, CONTAINER_NAME, SECRETSMANAGER_ARN, AWS_ROLE_ARN

### Permissions
- `id-token: write` (สำหรับ OIDC)
- `contents: read`

### Job 1: build-and-push
**Purpose**: Build Docker image แล้ว push ไป ECR

**Settings**:
- runs-on: ubuntu-latest
- environment: ตาม user ระบุ
- outputs: tag version สำหรับ deploy job

**Steps (ตามลำดับ)**:
1. **Checkout** — ใช้ `actions/checkout@v4`, fetch-depth 0, ref ขึ้นกับ event type (workflow_dispatch ใช้ main, push ใช้ tag ref)
2. **Extract version from tag** — ถ้า workflow_dispatch ใช้ input tag, ถ้า push ใช้ GITHUB_REF ตัด prefix `refs/tags/` ออก แล้วตัด `v.` prefix ถ้ามี เพื่อได้ version number
3. **Configure AWS credentials** — ใช้ `aws-actions/configure-aws-credentials@v2` กับ role-to-assume + region
4. **Login to ECR** — ใช้ `aws-actions/amazon-ecr-login@v2`
5. **Get secrets from Secrets Manager** — condition: เฉพาะเมื่อ `use_secrets_manager == 'true'` หรือ event เป็น push ดึง secret JSON แล้ว loop ทุก key เพื่อสร้าง `--build-arg` list
6. **Build, tag, push image** — build ด้วย Dockerfile ที่หาได้, tag ทั้ง version และ latest, push ทั้งสอง tag

### Job 2: deploy
**Purpose**: Deploy image ที่ build แล้วไปยัง ECS service

**Settings**:
- runs-on: ubuntu-latest
- needs: build-and-push
- environment: ตาม user ระบุ
- env: TASK_DEF_PATH = `.github/workflows/task-definition.json`

**Steps (ตามลำดับ)**:
1. **Checkout** — เหมือน job 1
2. **Configure AWS credentials** — เหมือน job 1
3. **Login to ECR** — เหมือน job 1
4. **Resolve image name** — สร้าง full image URI จาก ECR registry + repository + tag
5. **Download current task definition** — ใช้ `aws ecs describe-task-definition` query เฉพาะ taskDefinition
6. **Prepare Task Definition** — ลบ field `enableFaultInjection` ออกด้วย jq
7. **Clear environment variables from task definition** — ลบ `environment` array ออกจาก container definition ทั้งหมดด้วย jq (ตั้งเป็น `[]`) เพื่อป้องกันค่าซ้ำ/ชนกับค่าที่จะ inject ใหม่
8. **Inject secrets into task definition** — condition เหมือน step 5 ของ job 1 ดึง secret JSON + ARN แล้วสร้าง secrets array format `{"name": key, "valueFrom": "arn:...:key::"}` merge กับ secrets เดิมใน container definition (เก็บ secret เก่าที่ไม่ซ้ำ)
9. **Render task definition** — ใช้ `aws-actions/amazon-ecs-render-task-definition@v1` ใส่ image ใหม่
10. **Deploy task definition** — ใช้ `aws-actions/amazon-ecs-deploy-task-definition@v1` พร้อม `wait-for-service-stability: true` และ `force-new-deployment: true`
11. **Deployment summary** — แสดง image, tag, service, cluster ด้วย `::notice::`

## Actions ที่ใช้
- `actions/checkout@v4`
- `aws-actions/configure-aws-credentials@v2`
- `aws-actions/amazon-ecr-login@v2`
- `aws-actions/amazon-ecs-render-task-definition@v1`
- `aws-actions/amazon-ecs-deploy-task-definition@v1`

## Output
สร้างไฟล์ YAML ชื่อ `deploy-{environment}.yaml` (หรือตามที่ user ต้องการ) ที่พร้อมใช้งานใน `.github/workflows/`