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
- `aws_account_id` — AWS Account ID (12 หลัก) ใช้สำหรับหา profile ที่เหมาะสมใน ~/.aws/config

### ค้นหาจาก AWS Account ก่อน (ถ้าไม่ตรงให้ถาม user)
ค่าเหล่านี้ให้ลองค้นหาจาก AWS account โดยใช้ AWS CLI ก่อนถาม user:

- `ecs_cluster` — ค้นหาด้วย `aws ecs list-clusters --profile <profile> --region <region>` แล้วหา cluster ที่ชื่อใกล้เคียงกับ project_name ถ้าเจอหลายตัวหรือไม่แน่ใจ ให้ถาม user ว่าจะใช้ตัวไหน ถ้าไม่เจอเลยให้ user กรอกเอง
- `aws_role_arn` — ค้นหาด้วย `aws iam list-roles --profile <profile> --query "Roles[?contains(RoleName, 'github')]"` แล้วหา role ที่มีคำว่า `github` ในชื่อ ถ้าเจอหลายตัวให้ถาม user ว่าจะใช้ตัวไหน ถ้าไม่เจอให้ user กรอก ARN เอง
- `secretsmanager_arn` — ค้นหาด้วย `aws secretsmanager list-secrets --profile <profile> --region <region>` แล้ว filter ด้วยชื่อที่ใกล้เคียงกับ project_name ถ้าเจอหลายตัวให้ถาม user ถ้าไม่เจอให้ user กรอก ARN เอง
- `ecr_repository` — ค้นหาด้วย `aws ecr describe-repositories --profile <profile> --region <region>` แล้ว filter ด้วยชื่อที่ใกล้เคียงกับ project_name ถ้าเจอหลายตัวให้ถาม user ถ้าไม่เจอให้ derive จาก `{project_name}-{environment}`
- `ecs_service` — ค้นหาด้วย `aws ecs list-services --cluster <cluster> --profile <profile> --region <region>` แล้ว filter ด้วยชื่อที่ใกล้เคียงกับ project_name ถ้าเจอหลายตัวให้ถาม user ถ้าไม่เจอให้ derive จาก `{project_name}-{environment}`
- `container_name` — ค้นหาจาก task definition ของ service ด้วย `aws ecs describe-task-definition --task-definition <service-name> --profile <profile> --region <region>` แล้วดู `containerDefinitions[].name` ถ้าไม่เจอให้ derive จาก `{project_name}`

**Flow การค้นหา:**
1. อ่าน `~/.aws/config` หา profile ที่เหมาะสม (ดูจาก account/region)
2. แจ้ง user: "กรุณารัน `aws sso login --profile <profile>` ก่อนนะครับ" — รอ user ยืนยัน
3. ค้นหาแต่ละค่าด้วย AWS CLI
4. ถ้าเจอค่าที่ใกล้เคียง → เสนอให้ user เลือก
5. ถ้าไม่เจอ → ให้ user กรอกเอง

### Derive ได้ (ถ้า user ไม่ระบุ)
- `aws_region` → default: `ap-southeast-7`
- `tag_pattern` → `{environment}-v.*` แต่ถ้าเป็น prod จะเป็น `v.*`

### ค้นหาจากโครงสร้าง Repo (บังคับ)
- `dockerfile_path` — ค้นหาไฟล์ Dockerfile จากโครงสร้าง project (เช่น `./Dockerfile`, `./source/Dockerfile`, `./apps/*/Dockerfile`) ถ้าไม่เจอให้ถาม user เสมอ
- `docker_context` — ใช้ directory ที่ Dockerfile อยู่เป็น context ถ้าไม่เจอให้ถาม user เสมอ

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
5. **Build, tag, push image (with secrets)** — condition: เฉพาะเมื่อ `use_secrets_manager == 'true'` หรือ event เป็น push รวม get-secrets กับ docker build เป็น step เดียว ใช้ bash array เพื่อป้องกัน special characters ใน secret values:
   ```bash
   SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id ${{ env.SECRETSMANAGER_ARN }} --query SecretString --output text)
   BUILD_ARGS=()
   for key in $(echo "$SECRET_JSON" | jq -r 'keys[]'); do
     value=$(echo "$SECRET_JSON" | jq -r --arg k "$key" '.[$k]')
     BUILD_ARGS+=(--build-arg "${key}=${value}")
   done
   docker build "${BUILD_ARGS[@]}" -f <path> -t <tag> -t <latest> <context>
   ```
   **ห้ามใช้ string concatenation** (`BUILD_ARGS="$BUILD_ARGS --build-arg $key=$value"`) เพราะ secret values อาจมี `)` `?` `~` `'` `"` ที่ทำให้ bash syntax error
6. **Build, tag, push image (no secrets)** — condition: เมื่อ `use_secrets_manager == 'false'` และ event ไม่ใช่ push, build โดยไม่ดึง secrets

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

## Post-Generation Verification (AWS CLI)

หลังจากสร้างไฟล์ YAML เสร็จแล้ว ให้ทำการ verify ค่าต่อไปนี้กับ AWS จริง:

### Prerequisites
1. อ่าน AWS profile จากไฟล์ `~/.aws/config` เพื่อหา profile ที่เหมาะสม (ดูจาก account/region ที่ตรงกับ environment)
2. **แจ้ง user ให้รัน `aws sso login --profile <profile>` ก่อน** ถ้ายังไม่ได้ login — รอ user ยืนยันว่า login สำเร็จก่อนทำขั้นตอนถัดไป

### ค่าที่ต้อง Verify
ใช้ AWS CLI ตรวจสอบว่าชื่อที่ใช้ใน workflow มีอยู่จริงบน AWS:

| ค่า | คำสั่ง verify |
|-----|--------------|
| `ecr_repository` | `aws ecr describe-repositories --repository-names <name> --profile <profile> --region <region>` |
| `ecs_cluster` | `aws ecs describe-clusters --clusters <name> --profile <profile> --region <region>` |
| `ecs_service` | `aws ecs describe-services --cluster <cluster> --services <name> --profile <profile> --region <region>` |
| `container_name` | ดูจาก task definition ของ service: `aws ecs describe-task-definition --task-definition <task-def> --profile <profile> --region <region>` แล้วดู `containerDefinitions[].name` |
| `aws_role_arn` | `aws iam list-roles --profile <profile> --query "Roles[?contains(RoleName, 'github')]"` แล้วหา role ที่มีคำว่า `github` ในชื่อ ถ้าเจอหลายตัวให้ถาม user ว่าจะใช้ตัวไหน |
| `dockerfile_path` | ตรวจสอบว่าไฟล์ Dockerfile ที่ระบุใน workflow มีอยู่จริงใน repo โดยอ่านไฟล์นั้น ถ้าไม่เจอให้ถาม user ทันที |

### เมื่อชื่อไม่ตรง
- ถ้า verify แล้วไม่เจอ resource → ลอง list resources ที่ใกล้เคียง เช่น:
  - `aws ecr describe-repositories --profile <profile> --region <region>` แล้ว filter ชื่อที่คล้าย
  - `aws ecs list-services --cluster <cluster> --profile <profile> --region <region>`
  - `aws ecs list-clusters --profile <profile> --region <region>`
- ถ้าเจอชื่อที่ใกล้เคียง → **ถาม user ว่า "ไม่เจอ `<ชื่อที่ใช้>` บน AWS แต่เจอ `<ชื่อที่ใกล้เคียง>` ต้องการใช้ชื่อนี้แทนมั้ย?"**
- ถ้า user ยืนยัน → แก้ไขค่าใน YAML ที่สร้างไว้ให้ตรงกับชื่อจริงบน AWS
- ถ้าไม่เจอเลย → แจ้ง user ว่าไม่เจอ resource นี้บน AWS account/region นี้ อาจต้องสร้างใหม่หรือตรวจสอบ profile/region

### Flow
```
1. สร้าง YAML เสร็จ
2. อ่าน ~/.aws/config หา profile ที่เหมาะสม
3. แจ้ง user: "กรุณารัน `aws sso login --profile <profile>` ก่อนนะครับ แล้วบอกเมื่อ login เสร็จ"
4. รอ user ยืนยันว่า login แล้ว
5. Verify แต่ละค่าด้วย AWS CLI
6. ถ้าค่าไหนไม่ตรง → ถาม user + แก้ YAML
7. สรุปผลการ verify ให้ user
```
