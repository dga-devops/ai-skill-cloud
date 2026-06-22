---
name: deploy-iac-cdk
description: >-
  ขั้นตอนการขึ้น (onboard / deploy) ผ่าน IaC (AWS CDK) ใน repo นี้ ตามวิธีที่ผู้ใช้ทำจริง ทีละ step.
  ครอบคลุมทั้งการขึ้น service เต็มชุด (เช่น ecs+ecr+rds+...) และการขึ้น resource เดี่ยวๆ
  (เช่น rds อย่างเดียว, vpc, ecs cluster, alb, secrets). ใช้ skill นี้เมื่อผู้ใช้พูดถึงการ
  "ขึ้น service", "ขึ้น/สร้าง resource", "deploy", "เพิ่ม env (uat/prod)", หรือทำงานกับ IaC/CDK ใน repo นี้.
  (เอกสารนี้กำลังถูกสร้างทีละ step ตามที่ผู้ใช้สอน — ยังไม่สมบูรณ์)
---

# Onboard Service / Resource via IaC (CDK)

> สถานะ: **draft — กำลังเรียนรู้จากผู้ใช้ทีละ step**
> เขียนเฉพาะ step ที่ผู้ใช้สอน/ยืนยันแล้วเท่านั้น ห้ามเดา step ที่ยังไม่ได้สอน
>
> **Scope:** skill นี้ใช้ได้ทั้งการขึ้น service เต็มชุด **และ** การขึ้น resource เดี่ยวๆ
> (เช่น ขึ้นแค่ rds, vpc, ecs cluster, alb อย่างใดอย่างหนึ่ง) — workflow เดียวกัน
> ต่างกันแค่จำนวน resource ที่จะสร้างใน Step 2

## เมื่อไหร่ skill นี้ทำงาน (trigger)

เมื่อผู้ใช้บอกว่าจะ **deploy / ขอขึ้น service** หรือ **ขึ้น/สร้าง resource** ใดๆ ผ่าน IaC ใน repo นี้
ให้เริ่ม workflow ทันที

## ข้อมูลอ้างอิง (ใช้ตอนเขียน config — ห้ามเดา format เอง)

เวลาจะสร้างไฟล์ config ของ resource ใดๆ **ต้องอ้างอิงตัวอย่างจริงใน repo เสมอ** มี 2 แหล่ง:

1. **`examples/`** — ไฟล์ตัวอย่าง config พร้อมใช้ จัดตามโครงเดียวกับ `configs/`:
   - `examples/app/ecs/example-api.yaml`, `examples/app/ecs/example-worker.yaml`
   - `examples/data/ecr/example-ecr.yaml`
   - `examples/data/elasticache/example-elasticache.yaml`
   - `examples/shared-infra/alb/example-alb.yaml`
2. **`docs/*.md`** — design doc ของแต่ละ resource มี block ตัวอย่าง YAML + ตารางอธิบาย field
   ใช้เป็นแหล่งหลักสำหรับ resource ที่ยังไม่มีไฟล์ใน `examples/` (เช่น RDS Aurora, Secrets Manager, NLB, Route53)

แหล่งหลักในการลอกแบบคือ `examples/` และ `docs/` เท่านั้น

ส่วน config ของ service ที่ขึ้นไปแล้วใน `configs/` (เช่น `configs/app/ecs/dcs-api-service-disaster-event.yaml`)
เป็นของ service จริง **อย่าหยิบมาใช้เป็นต้นแบบถ้าไม่จำเป็น — ต้องถามผู้ใช้ก่อนทุกครั้ง**

## Workflow

### Step 1 — ยืนยัน AWS account แล้วให้ผู้ใช้ login ก่อน

> ถ้าผู้ใช้บอกมาแล้วว่า "ขอขึ้น ..." (service เต็มชุด หรือ resource เดี่ยว) ให้ดำเนินตามนั้นได้เลย
> **ยังไม่ต้องถามชื่อ (name) และ environment ตอนนี้** — สองอย่างนี้เป็น field ใน config
> เดี๋ยวไปถามตอนกรอก field ของ config (step ถัดไป) จะเหมาะกว่า

1. **ถาม AWS account** — ผู้ใช้กรอกมาเป็น **account id หรือ ชื่อ profile (name) หรือทั้งคู่** ก็ได้
   (เราไม่รู้ล่วงหน้าว่าจะได้อันไหน) จากนั้น **agent เป็นคนไปค้นเอง** ใน AWS config file ของเครื่อง:
   - path มาตรฐานคือ `~/.aws/config`
   - ตำแหน่งจริงขึ้นกับ OS ของเครื่อง — resolve home directory ให้ถูกตาม OS
     (เช่น Windows = `%USERPROFILE%\.aws\config`, macOS/Linux = `~/.aws/config`)
   - ไฟล์นี้อยู่ **นอก project** — ใช้ file-reading tool ปกติอาจไม่ได้ ให้ใช้ **คำสั่ง read-only**
     ผ่าน terminal อ่านแทน เช่น `type %USERPROFILE%\.aws\config` (Windows) หรือ `cat ~/.aws/config` (macOS/Linux)
     ห้ามใช้คำสั่งที่แก้ไขไฟล์
   - profile ใน config จะอยู่ในรูป `[profile <name>]` (หรือ `[default]`)
   - **วิธี match** ค่าที่ผู้ใช้กรอก:
     - ถ้ากรอก **ชื่อ** → match กับชื่อ profile ตรงๆ
     - ถ้ากรอก **account id** → หา profile ที่ account id ตรงกัน
       - SSO profile: ดูที่ key `sso_account_id`
       - profile ที่ใช้ role: ดู account id ใน `role_arn` (เช่น `arn:aws:iam::<account-id>:role/...`)
     - ถ้ากรอกมาทั้งคู่ → ใช้ยืนยันให้ตรงกัน (profile name นั้นต้องมี account id ตามที่บอก)
   - ถ้า **match ได้หลายอัน** → list ให้ผู้ใช้เลือก; ถ้า **ไม่เจอเลย** → แจ้งผู้ใช้และขอชื่อ profile อีกครั้ง

2. **ดูว่า profile เป็นแบบ SSO หรือ non-SSO** เพื่อบอกผู้ใช้ว่าจะ login ยังไง:
   - **SSO** (มี key `sso_start_url` / `sso_account_id` / `sso_role_name` หรือ section `sso-session`)
     → บอกผู้ใช้ login ด้วย:
     ```cmd
     aws sso login --profile <profile>
     ```
   - **non-SSO** (static credentials ใน `~/.aws/credentials`, หรือ `role_arn` + `source_profile`, หรือ access key)
     → ปกติไม่ต้อง `sso login`; credentials มีอยู่แล้ว แค่ยืนยันว่าใช้ได้ ถ้า static key หมดอายุ/ผิด
       ให้ผู้ใช้ตั้งใหม่ด้วย `aws configure --profile <profile>`

3. **ผู้ใช้เป็นคน login เอง** — agent ไม่รันคำสั่ง login ให้ บอกคำสั่งที่ถูกต้องให้ผู้ใช้
   แล้ว **หยุดรอ** จนกว่าผู้ใช้จะแจ้งกลับมาว่าเสร็จแล้ว อย่าทำ step ต่อไปก่อน

4. (เมื่อผู้ใช้แจ้งว่าเสร็จ) **agent เป็นคน verify เอง** — ห้ามเชื่อคำว่า "login เสร็จแล้ว" เฉยๆ
   รันคำสั่งนี้ (ใช้ได้ทั้ง SSO และ non-SSO) เพื่อตรวจว่า credentials ใช้งานได้จริง:
   ```cmd
   aws sts get-caller-identity --profile <profile>
   ```
   - **ต้อง match account** — ตรวจว่า `Account` ใน output ตรงกับ account id ที่ตั้งใจจะ deploy
     - ถ้าไม่ตรง → แจ้งผู้ใช้ว่า login ผิด account/ผิด profile แล้วให้ login ใหม่ (กลับไปข้อ 2–3) **อย่าไปต่อ**
   - ถ้าคำสั่ง error (เช่น token หมดอายุ / ยังไม่ได้ login) → แจ้งผู้ใช้ให้ login แล้ว **หยุดรอ** อีกครั้ง
   - ผ่านเมื่อ: คำสั่งสำเร็จ **และ** account ตรง → ค่อยไป Step 2

### Step 2 — ถามว่าต้องการสร้าง resource อะไรบ้าง

หลัง credentials ผ่านแล้ว ให้ถามผู้ใช้ว่าจะสร้าง resource อะไรบ้าง
(ปกติผู้ใช้จะบอกมาเองตั้งแต่แรก) — อาจเป็น **service เต็มชุด** (เช่น "ecs+ecr+rds")
หรือ **resource เดี่ยวๆ** (เช่น "rds อย่างเดียว", "vpc", "ecs cluster") ก็ได้

- รับมาเป็นรายการ resource ผู้ใช้พิมพ์สั้นๆ / คำย่อ / ชื่อเล่นได้ → **normalize** ให้ตรงกับ resource ที่ repo รองรับ
- ตีความ alias ที่พบบ่อย:
  - `redis` → **ElastiCache**
  - `secret` / `secrets` → **Secrets Manager**
  - `rds` / `aurora` → **RDS (Aurora)**
- ถ้า alias ไหน **ไม่แน่ใจ** ว่าหมายถึง resource ตัวไหน → **ถามผู้ใช้** อย่าเดา
- resource ที่ repo รองรับ (ดู `lib/stacks/`): vpc, nlb, alb, nlb-alb, ecs-cluster, ecs, ecr, rds (aurora), elasticache, secrets, route53
- สรุปรายการที่ normalize แล้วกลับไปยืนยันกับผู้ใช้ก่อนไปต่อ

### Step 3 — รวบรวมรายละเอียด config ของแต่ละ resource + ตัดสินลำดับและ mode

มี 2 ส่วน ทำควบคู่กัน:

#### 3.1 ถามรายละเอียด field ของแต่ละ resource

สำหรับ resource ที่จะสร้าง (จาก Step 2) ให้รวบรวมค่าที่ต้องกรอกใน config โดย
**ดู field ที่มีจากตัวอย่างจริง** (`examples/` + `docs/` ตามส่วน "ข้อมูลอ้างอิง") — ห้ามเดา field เอง
- **ถามทีละ resource** ไล่ตามลำดับ layer (ไม่รวบถามทุก field ทีเดียว เพราะ field เยอะ ผู้ใช้สับสน)
- รวมถึง `name`, `project`, และ `env` → ถามตอนนี้ (เป็น field ใน config; `name`/`project` มักแยกกัน ถาม `project` ด้วย)
- ถาม **เฉพาะค่าที่จำเป็น/ที่ไม่มี default** ก่อน ส่วนที่ doc มีค่าแนะนำตาม env อยู่แล้ว (เช่น Aurora capacity,
  ECR lifecycle, removalPolicy) ใช้ค่าแนะนำตาม env ได้เลย แล้วบอกผู้ใช้ว่าใช้ค่าไหน
- ค่าที่เป็น resource จริงจาก AWS (vpc id, subnets, cluster name, listener ARN, role ARN ฯลฯ) ต้องขอจากผู้ใช้
  ถ้ายังไม่มี — อย่าใส่ค่า placeholder แล้วไปต่อ

> **กฎเหล็ก: ห้ามเดา/คิดค่าเองในช่องที่ผู้ใช้ยังไม่ได้บอก** (บทเรียนจริง — โดนผู้ใช้ทักหลายรอบ)
> - **field ที่ไม่มี default ใน schema → ต้องถามผู้ใช้เสมอ** อย่าใส่ค่าที่ "ดูสมเหตุสมผล" เองแล้วไปต่อ
>   ตัวอย่างที่เคยพลาด: `port` (ECS required ไม่มี default), `routing.priority`, `routing.domain`,
>   `routing.targetGroupName`, `engine`/`engineVersion` ของ Aurora — ทั้งหมดนี้ **ถาม อย่าเดา**
> - **ค่าที่มี constraint** (เช่น `targetGroupName` max 32 chars, priority ห้ามซ้ำบน ALB เดียวกัน,
>   serverless cache name max 40) → บอก constraint ให้ผู้ใช้รู้ตอนถาม แล้วเช็คค่าที่ผู้ใช้ให้ว่าผ่าน
> - **ค่าที่ doc มี "ค่าแนะนำตาม env"** (Aurora capacity, ECR lifecycle/mutability, removalPolicy, log retention)
>   → ใช้ค่าแนะนำได้เลย แต่ **บอกผู้ใช้ว่าใช้ค่าไหน** เผื่อผู้ใช้อยากเปลี่ยน
> - ถ้าจะหยิบค่าจาก service อื่นมาใช้ซ้ำ (เช่น copy vpc/subnet/alb/iam/tags จาก service พี่น้อง) → **ถามยืนยันก่อน**
>   และค่าที่ **ห้าม copy ตรงๆ** เพราะต้อง unique ต่อ service: `priority` (ห้ามชนบน ALB เดียวกัน),
>   `domain`, `targetGroupName`

> **เลือก engine / engineVersion (Aurora, ElastiCache ฯลฯ) — ต้องเช็ค 2 ชั้น ก่อน deploy:**
> 1. **เช็คกับผู้ใช้** ว่าจะเอา engine อะไร version อะไร — อย่าเลือก version เองมั่ว
>    (บทเรียนจริง: ใส่ `aurora-postgresql 14.6` ไปเองทั้งที่ผู้ใช้ไม่ได้ระบุ แล้ว deploy fail เพราะ region ไม่มี)
> 2. **เช็คว่า region รองรับ version นั้นจริง** ด้วยคำสั่ง read-only ก่อนเขียน config/ก่อน deploy เช่น:
>    ```cmd
>    aws rds describe-db-engine-versions --engine aurora-postgresql --query "DBEngineVersions[?starts_with(EngineVersion,'14.')].EngineVersion" --output text --profile <profile> --region <region>
>    ```
>    ถ้า version ที่ผู้ใช้ขอไม่มีในรายการ → แจ้งผู้ใช้พร้อมเสนอ version ที่ใกล้เคียงที่ region รองรับ อย่าเดา

#### 3.2 เขียนไฟล์ config — ใส่ในไฟล์เดิม, ให้ผู้ใช้ review ก่อน

**โครงสร้างไฟล์:** 1 service = 1 ไฟล์ต่อ resource-type วางที่ `configs/{layer}/{resource}/{name}.yaml`
(โครงเดียวกับ `examples/`) โดย `{name}` = **top-level `name` (ชื่อ service)** ไม่ใช่ชื่อย่อย
(เช่น ไม่ใช่ `cacheName` / ชื่อ repo) — ชื่อไฟล์เดียวกันถูกใช้ซ้ำข้าม folder ของแต่ละ resource เช่น service
`dcs-api-service-disaster-event` จะมี `configs/app/ecs/dcs-api-service-disaster-event.yaml`
และ `configs/data/ecr/dcs-api-service-disaster-event.yaml`

**แต่ละไฟล์เก็บได้หลาย env** — ทุก env อยู่รวมในไฟล์เดียว (ตอน deploy ใช้ `--context env=` กรองเอา)
โครงไฟล์คือ top-level (`schemaVersion`, `name`, `project`, ...) + **array ของ entry** โดยแต่ละ entry
เป็นหนึ่ง env (มี field `env` ของตัวเอง) การ "เพิ่ม env" = **เพิ่ม entry ใหม่เข้า array นั้น**

> **ชื่อ array key + field ในแต่ละ entry ต่างกันตาม resource** (เช่น ECS ใช้ `environments`, ECR ใช้
> `repositories`, ElastiCache ใช้ `caches` ...) — **อย่าจำ/อย่าเดา** ให้เปิด **example + doc ของ resource นั้น**
> (ตามส่วน "ข้อมูลอ้างอิง") ดูโครงจริงก่อนเขียนทุกครั้ง วิธีนี้ยืดหยุ่นและไม่ outdated เมื่อ repo เพิ่ม/แก้ resource

**กฎการเขียน:**
- **มีไฟล์ของ service นั้นอยู่แล้ว** → เปิดไฟล์เดิม **append entry ของ env ใหม่เข้า array ที่ถูกต้อง**
  ของ resource นั้น **ห้ามสร้างไฟล์ใหม่ซ้ำ และห้ามแก้ entry ของ env เดิมที่ขึ้นไปแล้ว**
- **ยังไม่มีไฟล์** → สร้างใหม่ตามโครง example (top-level `name`/`project` + array ที่มี 1 entry)
- **ค่าต่าง env** อาจไม่เหมือนกัน (เช่น ECR: uat = MUTABLE/Delete, prod = IMMUTABLE/Retain;
  ECS: uat กับ prod คนละ account) → ใช้ค่าแนะนำตาม env จาก doc
- **ให้ผู้ใช้ review ก่อนเขียน/ก่อนไปต่อเสมอ** — เสนอเนื้อหา config ที่จะเขียน แล้วรอผู้ใช้ยืนยัน
  (ไม่เขียนทับ/แก้ไฟล์จริงโดยไม่ผ่านสายตาผู้ใช้)

#### 3.3 agent ตัดสินลำดับ + mode เอง (ไม่โยนถามผู้ใช้ตอน runtime)

**ลำดับการสร้าง (dependency):** ไหลตาม layer
Network (VPC, Route53) → Shared Infra (ALB, NLB, ECS Cluster) → Data (ECR, RDS, ElastiCache, Secrets) → App (ECS)
หลัก: resource ที่ถูก ref (export ค่า) ต้องมาก่อน resource ที่ ref (import) — ดู Outputs/Exports ในแต่ละ doc

**เลือก mode ของแต่ละ ref:**
- `auto` — ref ไป resource ที่**กำลังสร้างพร้อมกันใน batch นี้** และอยู่ **account+region เดียวกัน**
  (CDK import จาก CloudFormation export + จัดลำดับ deploy ให้เอง)
- `manual` — resource **มีอยู่แล้ว** (ไม่ได้สร้างในรอบนี้) → ใส่ค่า (ARN/id) ตรงๆ
- `lookup` — เฉพาะ VPC เมื่ออยากให้ CDK ค้น AWS ตอน synth (ต้องมี credentials ที่ access ได้)
- ใช้ `auto` **เท่าที่สมควร** ไม่ต้องฝืนใช้ทุกจุด เป้าหมายคือ deploy แล้วใช้งานได้จริง

**การเชื่อมต่อระหว่าง data resource (RDS / ElastiCache / Secrets / ECR) กับ ECS:**
- resource เหล่านี้**ไม่ผูกแน่น**กับ ECS — แค่ Security Group เปิดให้ต่อถึงกันได้ก็พอ
- จึง**ไม่ต้องกังวล circular dependency** กรณีสร้าง data + ECS พร้อมกัน:
  ให้ data resource เปิด ingress แบบที่ไม่ต้องวนรอ SG ของ ECS (เช่น `allowFromCidrs` ด้วย VPC CIDR)
  ส่วนความถูกต้องของการต่อถึงกันจะ **verify ใน step หลัง** อยู่แล้ว
- ใช้ `allowFromSecurityGroups: mode auto ref ECS` เฉพาะเมื่อ ECS **มีอยู่แล้ว** (deploy คนละรอบ)

> **บทเรียนจริง: `allowFromSecurityGroups: mode auto ref <ECS-stack>` ไม่ได้สร้าง CDK dependency**
> โค้ด repo ใช้ `cdk.Fn.importValue("<ref>-ECS-SgId")` เป็น string ตรงๆ → CDK **มองไม่เห็น dependency**
> จึงไม่จัดลำดับ deploy ให้ ECS มาก่อน ผลคือถ้า `cdk deploy --all` มันจะสร้าง data resource ก่อน ECS แล้ว
> **fail เพราะยังไม่มี export `<ref>-ECS-SgId`** (`No export named ... found`)
> **ทางแก้เมื่อผู้ใช้ยืนยันว่าจะเชื่อมด้วย SG เท่านั้น (ไม่เอา VPC CIDR):** แตก deploy เป็น **2 เฟส**
>   1. เฟส 1: deploy **ECS ก่อน** (`npx cdk deploy <name>-<env>-ECS ...`) ให้มี export `...-ECS-SgId`
>   2. เฟส 2: deploy data resource ที่ ref SG ของ ECS (`<name>-<env>-Aurora <name>-<env>-ElastiCache ...`)
>   ตรวจให้ ECS ขึ้น `CREATE_COMPLETE` ก่อนค่อยทำเฟส 2
> ถ้าผู้ใช้ **ไม่ได้ระบุ** ว่าต้อง SG-only ก็ใช้ `allowFromCidrs` (VPC CIDR) deploy รอบเดียวจบได้
> — แต่ **ห้ามเปลี่ยนไปใช้ CIDR เองถ้าผู้ใช้สั่งให้ใช้ SG** ให้ทำ phased deploy แทน

> **บทเรียนจริง: ชื่อ Security Group ห้ามซ้ำใน VPC เดียวกัน**
> stack code ตั้งชื่อ SG จากชื่อ resource เช่น ECS = `${name}-${env}-sg`, Aurora = `${clusterName}-${env}-sg`,
> ElastiCache = `${cacheName}-${env}-sg` → ถ้าตั้ง `clusterName`/`cacheName` **เท่ากับ** ชื่อ service (`name`)
> จะได้ชื่อ SG เดียวกับ ECS → deploy fail (`Security Group with <name>-<env>-sg already exists`)
> **วิธีกัน:** ตั้ง `clusterName`/`cacheName` (และชื่อย่อยอื่นที่ถูกใช้ตั้งชื่อ SG) **ไม่ให้ชนกัน** หรือเติม suffix
> เช่น `-db` / `-cache` (เคสนี้ผู้ใช้เลือกแก้ที่ stack code ให้เติม suffix อัตโนมัติ — ดูส่วน "บทเรียน/ข้อควรระวัง")

**Cross-account: ยังไม่รองรับ** — ถ้า resource ต้อง ref ข้าม account/region ให้ **แจ้งผู้ใช้** ว่าเคสนี้
ยังไม่รองรับ (ต้องใช้ transit gateway / VPC endpoint ซึ่งยังไม่ทำ) อย่าพยายาม workaround เอง

### Step 4 — ยืนยันกับผู้ใช้แล้ว deploy

หลังผู้ใช้ review config (Step 3.2) แล้ว ก่อน deploy ให้ **ถาม/ยืนยันกับผู้ใช้ให้ชัดเจน** ว่า:
1. review **ผ่าน**แล้วหรือยัง (พร้อม deploy ไหม)
2. จะ deploy **env ไหน** (เช่น uat / prod)
3. **project (name) อะไร** — เอาให้ชัวร์ว่าตรงกับที่ตั้งใจ ไม่ deploy ผิดตัว/ผิด env

> deploy เป็น action ที่กระทบ AWS account จริง — ห้าม deploy ก่อนได้รับการยืนยันทั้ง 3 ข้อ
> **ผู้ใช้เป็นคนรันคำสั่ง deploy เอง** (agent ไม่รันให้) เพราะ `cdk deploy` อาจมี approval prompt
> ถาม y/n กลางคัน (เมื่อมีการเปลี่ยน IAM/Security Group) ซึ่ง agent ตอบ prompt นั้นไม่ได้ จะค้าง
> — agent มีหน้าที่บอกคำสั่งที่ถูกต้องให้ผู้ใช้ แล้วรอผู้ใช้แจ้งผล

**คำสั่ง deploy** (อ้างอิงจาก `docs/AWS CDK Implementation Guide.md` — context filter):

ก่อน deploy ให้ **agent รัน `cdk diff` ก่อนเสมอ** เพื่อดูว่าจะสร้าง/เปลี่ยนอะไรบ้าง
(`cdk diff` เป็น read-only ไม่มี prompt agent รันเองได้ — ใช้ context filter ชุดเดียวกับ deploy):

```cmd
npx cdk diff --context env=<env> --context project=<name> --profile <profile>
```

จากนั้น **บอกคำสั่ง deploy ให้ผู้ใช้รันเอง** แล้วหยุดรอผู้ใช้แจ้งผล:

```cmd
npx cdk deploy --all --context env=<env> --context project=<name> --profile <profile>
```

- **ต้องใส่ `--context env=` เสมอ** เมื่อ repo มีหลาย account — ไม่งั้น CDK จะ synth ทุก account แล้ว fail
- `--context project=<name>` กรองเฉพาะ service นี้ (ใส่ผิดชื่อ CDK จะ error ว่าไม่พบ project — ช่วยจับ typo)
- `--profile <profile>` ใช้ profile เดียวกับที่ login/verify ผ่านใน Step 1
- `--all` ให้ CloudFormation deploy ตามลำดับ dependency อัตโนมัติ (resource ที่ `auto` ref กัน)
- ถ้าต้องการเจาะจง: ระบุชื่อ stack ตรงๆ (`<name>-<env>-ECS <name>-<env>-ECR ...`)
  หรือ wildcard (`"<name>-<env>-*"`) ก็ได้ — ดูรูปแบบใน doc

**เมื่อผู้ใช้แจ้งว่า deploy เสร็จ:** ตรวจว่าทุก stack `CREATE_COMPLETE`/`UPDATE_COMPLETE`

> **ขั้นตอนเช็ค stack status (ทำเสมอ — ทั้งหลัง deploy สำเร็จ และตอน error):** อย่าเชื่อแค่คำว่า "เสร็จแล้ว"
> ของผู้ใช้ ให้ **agent รันเอง** (read-only) เพื่อดูสถานะจริงของทุก stack ของ service นี้:
> ```cmd
> aws cloudformation describe-stacks --profile <profile> --region <region> --query "Stacks[?starts_with(StackName, '<name>-<env>')].{Name:StackName,Status:StackStatus}" --output table
> ```
> ใช้คำสั่งนี้ทั้ง: (ก) ยืนยันว่าทุก stack `CREATE_COMPLETE`/`UPDATE_COMPLETE` ก่อนไป Step 5,
> (ข) ตอน deploy fail เพื่อดูว่า stack ไหนสำเร็จ/stack ไหนค้าง

**ถ้า deploy error:**
- **แจ้ง error ให้ผู้ใช้แล้วหยุดทำงาน** (อย่าพยายาม workaround/แก้วนเอง) — แต่ **วิเคราะห์ root cause**
  ให้ผู้ใช้ก่อนเสมอ (เช่น export ไม่เจอ = ลำดับ deploy, ชื่อ SG ซ้ำ = naming collision,
  version not found = engine/region ไม่รองรับ) อย่าแค่ paste error
- **แจ้งผู้ใช้ด้วยว่า resource/stack ที่ deploy สำเร็จไปแล้วก่อนหน้า error จะยังอยู่ ไม่ถูกลบ**
  (CloudFormation rollback เฉพาะ stack ที่ fail — stack อื่นที่ complete ไปแล้วยังคงอยู่)
  เพื่อให้ผู้ใช้รู้สถานะจริงและตัดสินใจขั้นต่อไป

> **จัดการ stack ที่ค้างก่อน deploy ใหม่:** ถ้า stack อยู่สถานะ `ROLLBACK_COMPLETE` (สร้างครั้งแรกแล้ว fail)
> หรือ `REVIEW_IN_PROGRESS` (changeset ค้าง) — stack เหล่านี้ **ว่างเปล่า สร้าง resource ไม่สำเร็จ** ต้อง **ลบทิ้งก่อน**
> ถึงจะ deploy ใหม่ได้ (CloudFormation สร้างทับ stack ที่ `ROLLBACK_COMPLETE` ไม่ได้):
> ```cmd
> aws cloudformation delete-stack --stack-name <stack> --profile <profile> --region <region>
> ```
> หลังสั่งลบ ให้ **รอแล้ว describe-stacks ซ้ำ** ยืนยันว่าหายจริง (และ stack ที่สำเร็จก่อนหน้ายังอยู่ครบ) ก่อนบอกผู้ใช้ deploy ใหม่
> — การลบ stack ที่ว่าง (rollback/review) ปลอดภัย แต่ **อย่าลบ stack ที่ `CREATE_COMPLETE`** โดยไม่ถามผู้ใช้

### Step 5 — ตรวจสอบหลัง deploy ด้วย AWS CLI (verify connectivity)

เมื่อ deploy ครบทุก resource ตามที่ต้องการแล้ว ให้ **agent ตรวจสอบเองด้วย AWS CLI** (เป็นคำสั่ง
read-only describe/get — agent รันได้ ไม่กระทบ resource) ใช้ `--profile <profile>` เดิม

**กรณีสร้าง ECS พร้อม data resource อื่น (RDS / ElastiCache / Secrets) ในรอบเดียวกัน** —
ตรวจว่า ECS เชื่อมต่อ resource เหล่านั้นได้จริงหรือไม่ โดยดูจาก:

- **Security Group** — ECS task SG ต้องต่อไปยัง data resource ได้ และ data resource SG ต้อง allow inbound
  จาก ECS SG (หรือจาก CIDR ที่กำหนดใน config) บน port ที่ถูกต้อง (เช่น RDS 5432/3306, Redis 6379)
  - ดู ingress/egress rule ของ SG เช่น `aws ec2 describe-security-groups --group-ids <sg-id> --profile <profile>`
  - เทียบว่า port + source ตรงกับที่ออกแบบไว้ใน config (`security.allowFromCidrs` / `allowFromSecurityGroups`)
- **IAM role** — โดยเฉพาะ execution role ของ ECS ต้องมีสิทธิ์อ่าน Secret ที่ผูกไว้
  (เช่น `secretsmanager:GetSecretValue`) และเข้าถึง ECR ได้
  - ดู policy ที่ผูกกับ role เช่น `aws iam list-attached-role-policies` / `aws iam get-role-policy`

> **ตรวจสิทธิ์อ่าน Secret ให้ครบ "ทั้ง 2 role" — อย่าเช็คแค่ execution role** (บทเรียนจริง: เคยตอบว่า verify
> ครบทั้งที่ลืมเช็ค task role → ผู้ใช้ทักว่า "ได้ดู role ว่าต่อ secret ได้มั้ยรึยัง")
> - **execution role** — ใช้ตอน ECS **inject secret ผ่าน task definition** (start task)
> - **task role** — ใช้ตอน **container อ่าน secret เองตอน runtime ผ่าน AWS SDK** (`getSecretValue`)
>   สำคัญเพราะ schema ECS ของ repo **ยังไม่รองรับ inject secret ผ่าน task def** (Future Enhancement)
>   ดังนั้นจริงๆ container ต้องอ่านเองด้วย task role → **task role ต้องอ่าน secret ได้ด้วย**
> - **อย่าเดาจากชื่อ policy** ว่าผ่าน/ไม่ผ่าน — ใช้ **policy simulator** เช็คตรงๆ กับ ARN จริงของ secret ทุกตัว
>   (รวม secret ที่ Aurora generate เอง ชื่อ `<clusterName>-<env>-credentials`):
>   ```cmd
>   aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names secretsmanager:GetSecretValue --resource-arns <secret-arn-1> <secret-arn-2> --profile <profile> --query "EvaluationResults[].{Resource:EvalResourceName,Decision:EvalDecision}" --output json
>   ```
>   `allowed` = ผ่าน, `implicitDeny`/`explicitDeny` = ไม่ผ่าน
> - **ถ้า task role อ่านไม่ได้ และผู้ใช้ต้องการให้อ่านได้** → เพิ่ม **inline policy แบบ additive + scope แคบ**
>   (เฉพาะ secret ARN ของ service นี้ ใช้ wildcard suffix `-*` เผื่อ ARN suffix เปลี่ยนตอนสร้างใหม่):
>   ```cmd
>   aws iam put-role-policy --role-name <role> --policy-name <name>-<env>-secrets-read --policy-document file://<policy>.json --profile <profile>
>   ```
>   แล้ว simulate ซ้ำยืนยันว่า `allowed` + ลบไฟล์ policy ชั่วคราวทิ้ง
>   **ข้อควรระวัง:** task/execution role มักเป็น **role กลางที่หลาย service ใช้ร่วม** (เช่น `devsecops-...-task-role`
>   ที่เป็น `manual` ใน config ไม่ได้ถูกจัดการโดย CDK) — การแก้ต้องเป็น **additive scope แคบเท่านั้น**
>   แจ้งผู้ใช้เรื่อง shared role + ความเสี่ยง และบอกคำสั่ง rollback (`delete-role-policy`) ไว้ด้วย
- **ตรวจจากจุดอื่นเพิ่มได้ถ้ามี** เช่น ECS service/task running จริงไหม, task definition ผูก secret ARN /
  environment variable ที่ชี้ไป endpoint ของ DB/cache ถูกต้องไหม, target group health (ถ้าเป็น service)

หลักการ: เทียบ "สิ่งที่ deploy จริงบน AWS" กับ "สิ่งที่ตั้งใจไว้ใน config/doc" ว่าตรงกันและต่อถึงกันได้
ถ้าเจอจุดที่ไม่ตรง/ต่อไม่ถึง → สรุปให้ผู้ใช้ทราบพร้อมจุดที่เป็นปัญหา

### Step 5.1 — Disable rotation สำหรับ Aurora ที่ใช้ rds-managed credentials

> ทำ **ต่อจาก Step 5** (หลัง verify connectivity ผ่าน) — เฉพาะเมื่อ Aurora config ใช้ `credentials.management: "rds-managed"`
> (ซึ่งเป็น default) เพราะ RDS-managed จะเปิด rotation ทุก 7 วันอัตโนมัติ ซึ่งเราไม่ต้องการ

**ขั้นตอน (agent รันเอง — เป็น write operation แต่ไม่กระทบ data/connectivity):**

1. **ดึง Secret ARN** จาก CloudFormation output ของ Aurora stack:
   ```cmd
   aws cloudformation describe-stacks --stack-name <name>-<env>-Aurora --profile <profile> --region <region> --query "Stacks[0].Outputs[?OutputKey=='SecretArn'].OutputValue" --output text
   ```

2. **ตรวจว่า rotation เปิดอยู่หรือไม่** (read-only):
   ```cmd
   aws secretsmanager describe-secret --secret-id <secret-arn> --profile <profile> --region <region> --query "{RotationEnabled:RotationEnabled,RotationRules:RotationRules}" --output json
   ```
   - ถ้า `RotationEnabled: true` → ไปข้อ 3
   - ถ้า `RotationEnabled: false` หรือไม่มี rotation → ข้ามได้เลย (ปกติจะเป็น true เพราะ RDS เปิดให้ default)

3. **Disable rotation:**
   ```cmd
   aws secretsmanager cancel-rotate-secret --secret-id <secret-arn> --profile <profile> --region <region>
   ```

4. **Verify ว่า rotation ปิดแล้ว** (read-only):
   ```cmd
   aws secretsmanager describe-secret --secret-id <secret-arn> --profile <profile> --region <region> --query "RotationEnabled" --output text
   ```
   - ต้องได้ `False` → ผ่าน
   - ถ้ายัง `True` → แจ้งผู้ใช้ว่า disable ไม่สำเร็จ

> **หมายเหตุ:** `cancel-rotate-secret` เป็น safe operation — แค่ปิด schedule ไม่ได้แก้ password หรือลบ secret
> agent รันเองได้โดยไม่ต้องถามผู้ใช้ก่อน เพราะเป็นส่วนหนึ่งของ config ที่ตกลงไว้แล้ว (rds-managed + ไม่ rotate)

### Step 6 — (Optional) ถามว่าจะสร้าง deployment workflow ด้วยไหม

เป็น **option เสริม** หลังจาก deploy + verify ผ่านแล้ว — ถามผู้ใช้ว่าต้องการสร้าง
**deployment workflow** (GitHub Actions YAML สำหรับ deploy ไป ECS) ด้วยหรือไม่

- ถ้า **เอา** → ใช้ skill **`ecs-workflow`** (skill เฉพาะสำหรับ generate GitHub Actions workflow YAML
  deploy ไป AWS ECS) ทำต่อ — ส่งต่อค่าที่ได้จาก step ก่อนหน้า (service name, env, account/region,
  ECR repo, ECS service/cluster ฯลฯ) ให้ skill นั้นใช้
- ถ้า **ไม่เอา** → ไปขั้นปิดงาน

## เมื่อจบงาน (ปิดงาน) — แจ้งเรื่อง DNS (CNAME / Route53)

ไม่ใช่ step เชิงเส้น แต่เป็นสิ่งที่ **ต้องแจ้งผู้ใช้เสมอ** ก่อนถือว่างานเสร็จ:

- **อย่าลืม map CNAME** ของ domain ที่ตั้งไว้ (เช่นใน `routing.domain` ของ ECS service) ให้ชี้มาที่ ALB
  ไม่งั้นเรียก service ผ่าน domain ไม่ได้
- หรือถ้าต้องการ ก็ **มี option ให้สร้าง DNS record ผ่าน Route53** ด้วย skill นี้เองได้
  (repo รองรับ Route53 stack — ดู `docs/Route53 Design.md`) → ถ้าผู้ใช้เอา **ไม่ต้องเริ่ม workflow ใหม่**
  เพราะข้อมูลที่จำเป็น (account/profile/env/name/infra refs) มีครบจาก step ก่อนหน้าแล้ว ให้ทำเฉพาะส่วนที่เหลือ:
  1. สร้าง config ของ `route53` (อ้างอิง `docs/Route53 Design.md` — target ชี้ไป ALB) ตามวิธีใน Step 3.2
  2. ให้ผู้ใช้ review config
  3. deploy + verify ตาม Step 4–5

---

## บทเรียน / ข้อควรระวัง (จาก session จริง — อ่านก่อนเริ่มทุกครั้ง)

สรุปจุดที่เคยพลาดและถูกผู้ใช้ทัก เพื่อไม่ให้ซ้ำ:

1. **ห้ามเดาค่า config เอง** — field ที่ผู้ใช้ยังไม่ได้บอกและไม่มี default → **ถาม** (port, priority, domain,
   targetGroupName, engine/version ฯลฯ) ดูรายละเอียดใน Step 3.1

2. **เลือก engine/version ต้องเช็คกับผู้ใช้ + เช็คว่า region รองรับ** ก่อน deploy (ใช้ `describe-db-engine-versions`)
   — เคยใส่ `aurora-postgresql 14.6` เองแล้ว fail เพราะ region ไม่มี (region นี้มี 14.13/14.15/14.17/14.18/14.19/14.20/14.22)

3. **ลำดับ deploy เมื่อเชื่อม SG ด้วย `allowFromSecurityGroups: auto`** — CDK มองไม่เห็น dependency
   (เป็น `Fn.importValue` string) → ต้อง **phased deploy** (ECS ก่อน → data resource ทีหลัง) ดู Step 3.3

4. **ชื่อ SG ห้ามซ้ำใน VPC** — `clusterName`/`cacheName` อย่าตั้งเท่ากับ service `name` ไม่งั้นชนกับ SG ของ ECS
   - **วิธีที่ผู้ใช้เลือกในเคสนี้:** แก้ที่ **stack code** ให้เติม suffix อัตโนมัติ — config ใส่ชื่อ service ตรงๆ ได้
     - `lib/stacks/aurora-stack.ts`: `clusterFullName = ${config.clusterName}-db-${config.env}`
     - `lib/stacks/elasticache-stack.ts`: `cacheFullName = ${config.cacheName}-cache-${config.env}`
   - ผลลัพธ์: Aurora SG = `<name>-db-<env>-sg`, Cache SG = `<name>-cache-<env>-sg` ไม่ชนกับ ECS = `<name>-<env>-sg`
   - เช็ค constraint ความยาวด้วย (serverless cache name max 40, cluster id max 63)

5. **เช็ค stack status เสมอ** ด้วย `describe-stacks` ทั้งหลัง deploy และตอน error — และ **ลบ stack ที่ค้าง**
   (`ROLLBACK_COMPLETE` / `REVIEW_IN_PROGRESS`) ก่อน deploy ใหม่ ดู Step 4

6. **verify ต้องครบจริงก่อนบอกผู้ใช้ว่า "เสร็จ/ผ่าน"** — โดยเฉพาะ **task role อ่าน secret ได้ไหม**
   (ไม่ใช่แค่ execution role) ใช้ policy simulator ยืนยัน อย่าเดาจากชื่อ policy ดู Step 5

---

## ยังไม่สอน — เผื่ออนาคต

> ยังมีกรณีที่ยังไม่ได้สอน เช่น การ verify กรณี **ไม่ได้สร้าง ECS พร้อมกัน**
> (สร้าง resource เดี่ยวๆ หรือ ECS ที่ ref ของเดิมที่มีอยู่แล้ว) — รอผู้ใช้สอนเพิ่มภายหลัง
