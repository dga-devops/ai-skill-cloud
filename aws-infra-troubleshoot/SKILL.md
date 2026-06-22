---
name: aws-infra-troubleshoot
description: Troubleshoot and diagnose AWS infrastructure issues, especially ECS services. Use this skill when the user reports a service is down, unhealthy, unreachable, or not working as expected on AWS. Also triggers when the user mentions health check failures, ECS task failures, service connectivity problems, ALB issues, security group misconfigurations, WAF blocks, or wants to investigate why an AWS service is broken. Use even if the user just says a service name and says it's not working.
---

# AWS Infrastructure Troubleshooter

วินิจฉัยและหาสาเหตุปัญหา infrastructure บน AWS โดยเฉพาะ ECS services ทำงานเป็นขั้นตอนตามลำดับ และรายงานผลให้ user ตัดสินใจก่อนแก้ไขเสมอ

## หลักการสำคัญ

- ห้ามแก้ไขอะไรเองโดยไม่ได้รับอนุญาตจาก user
- เมื่อพบสาเหตุ ให้รายงาน: เจออะไร → สาเหตุคืออะไร → แนะนำวิธีแก้
- ให้ user เลือกว่าจะแก้เอง หรือให้ AI แก้ให้
- ห้ามเดาข้อมูลที่ไม่รู้ (เช่น cluster name) ถ้าหาไม่เจอให้ถาม user
- ห้ามคิด/เดา AWS CLI commands หรือ output format เอง — ต้องใช้ AWS Documentation MCP เพื่อยืนยันว่า command มีจริง, parameters ถูกต้อง, และ response format เป็นอย่างที่คาดหวังก่อนรันเสมอ

## การใช้ AWS Documentation

ก่อนรัน AWS CLI command ใดๆ ให้ใช้ AWS Documentation MCP เพื่อ:
1. ยืนยันว่า command/subcommand มีอยู่จริง
2. ตรวจสอบ parameters ที่ต้องใช้และ format ที่ถูกต้อง
3. ดู response structure เพื่อรู้ว่าจะ parse ผลลัพธ์ยังไง

ห้ามสมมติว่า command ทำงานแบบที่คิด — ดู doc ก่อนเสมอ เพราะ AWS CLI มีการเปลี่ยนแปลง parameters และ output format บ่อย

## ขั้นตอนที่ 1: ระบุ Account & เลือก AWS Profile

ถาม user ว่าจะทำงานกับ account ไหน (เช่น `301109183009`)

เมื่อได้ account ID แล้ว:
1. อ่านไฟล์ `~/.aws/config` (path ตาม OS ของ user เช่น Windows: `%USERPROFILE%\.aws\config`, macOS/Linux: `~/.aws/config`)
2. หา profile ที่มี `sso_account_id` ตรงกับ account ID ที่ user ให้มา
3. ใช้ profile นั้นเป็น `--profile <profile_name>` ในทุก aws cli command ต่อไป

ถ้ายังไม่ได้ login ให้แจ้ง user:

    กรุณา login ก่อนนะครับ:
    aws sso login --profile <profile_name>

รอจน user ยืนยันว่า login สำเร็จแล้วค่อยทำต่อ

## ขั้นตอนที่ 2: ระบุ Service & หา Cluster

ถาม user ว่า service ชื่ออะไรที่มีปัญหา (เช่น `dcs-admin-disaster-event`)

หา cluster ของ service ตามลำดับ:

### วิธีที่ 1: ใช้ MCP Inventory Database

ใช้ MCP ที่ต่อกับ inventory database เพื่อ query หา cluster ของ service นั้น

การต่อ DB ต้องใช้ SSM port forwarding:

    aws ssm start-session --target "i-0ab060aa33a04ef3d" --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters "host=\"itc-devsecops-instance-1.crya4aswcsbu.ap-southeast-7.rds.amazonaws.com\",portNumber=\"5432\",localPortNumber=\"5433\""

เมื่อต่อได้แล้ว query หา service -> cluster mapping จาก DB

### วิธีที่ 2: ถาม User

ถ้าต่อ MCP ไม่ได้ หรือ query แล้วไม่เจอข้อมูล -> ถาม user ว่า service อยู่ cluster ไหน

ห้ามเดา cluster name เด็ดขาด

## ขั้นตอนที่ 3: ตรวจสอบ Health Check

ใช้ AWS Documentation MCP เพื่อยืนยัน command ที่ถูกต้องสำหรับ:
- ดู ECS service status
- ดู target group health
- ดู health check configuration

เริ่มจากดู health check status ของ ECS service/target group

### กรณี Health Check Fail

**ถ้า status code ไม่ตรง** (เช่น app return 201 แต่ HC expect 200):
- ดู health check configuration ว่าตั้ง matcher ไว้อะไร
- เทียบกับ response ที่ app ส่งกลับจริง
- รายงาน user ว่า HC expect อะไร แต่ app ตอบอะไร

**ถ้า request timeout**:
- ดู Security Group ของ ECS tasks
- ดู Security Group ของ ALB
- ตรวจสอบ:
  - ALB SG อนุญาต inbound จาก internet/client ไหม
  - ECS SG อนุญาต inbound จาก ALB SG ไหม
  - ECS SG อนุญาต outbound ไป internet ไหม (สำหรับ pull image, ต่อ external services)
  - มี NAT Gateway / VPC endpoints ที่จำเป็นไหม

## ขั้นตอนที่ 3.5: กรณี Deployment Rollback

ถ้า ECS service มีการ rollback (deployment failed) ให้ตรวจสอบ task ที่เกิดปัญหา:

1. **ดู service events** — หา deployment ที่ fail และ rollback event
2. **หา stopped tasks** — list tasks ที่ status เป็น STOPPED ใน service นั้น
3. **ดู stopped reason** — describe task ที่ stopped เพื่อดูว่าหยุดเพราะอะไร (เช่น container exit code, health check failure, OOM killed)
4. **ดู logs ของ task ที่ fail** — ใช้ task ID ไปหา log stream ใน CloudWatch Logs เพื่อดูว่า container log บอกอะไรก่อนตาย

ใช้ AWS Documentation MCP เพื่อยืนยัน command สำหรับ:
- List tasks ที่ stopped ใน service/cluster
- Describe task เพื่อดู stoppedReason, stopCode, container exit code
- หา log stream name จาก task ID (format ปกติคือ prefix/container-name/task-id)

สาเหตุที่พบบ่อยจาก rollback:
- Container crash ตอน startup (exit code 1) — ดู logs จะเห็น error
- Health check fail ซ้ำจนถูก kill — ดูว่า app start ทันก่อน HC timeout ไหม
- OOM killed (exit code 137) — container ใช้ memory เกิน limit ที่ตั้งไว้ใน task definition
- Image pull failure — image tag ไม่มีใน ECR หรือ permission ไม่พอ
- Secret/environment variable หาย — ต่อ Secrets Manager หรือ Parameter Store ไม่ได้

## ขั้นตอนที่ 4: ดู Logs

ใช้ AWS Documentation MCP เพื่อยืนยัน command สำหรับดู CloudWatch Logs

ดู logs ของ service เพื่อหา error — สิ่งที่ต้องมองหา:
- Connection refused / timeout ไป database
- Connection refused / timeout ไป Redis
- Permission denied / access denied
- Out of memory
- Unhandled exceptions ตอน startup

## ขั้นตอนที่ 5: ตรวจสอบ WAF

ตรวจสอบว่ามีการใช้ WAF หรือไม่:
1. ดูจาก MCP inventory database
2. ถ้าไม่มีข้อมูลใน DB -> ถาม user

ถ้ามี WAF — ใช้ AWS Documentation MCP เพื่อหา command ที่ถูกต้องสำหรับ:
- ดู Web ACL configuration
- ดู sampled requests ที่โดน block

## ขั้นตอนที่ 6: รายงานผล

เมื่อพบสาเหตุแล้ว รายงานให้ user ในรูปแบบ:

    ## สรุปปัญหา
    - Service: <ชื่อ service>
    - Cluster: <ชื่อ cluster>
    - สถานะ: <สถานะปัจจุบัน>

    ## สาเหตุที่พบ
    <อธิบายสาเหตุ>

    ## วิธีแก้ไข
    <แนะนำวิธีแก้ พร้อม command ที่ต้องรัน>

    ## ต้องการให้ดำเนินการไหม?
    - แก้ไขเอง (ผมจะให้ command ที่ต้องรัน)
    - ให้ AI แก้ให้ (ผมจะรัน command ให้)

### กรณี Health Check ผ่านแต่ Service ไม่ทำงานตามคาดหวัง

ถ้า health check ผ่านหมด แต่ user บอกว่า service ทำงานไม่ถูกต้อง:

แจ้ง user ว่า:
> Infrastructure ทำงานปกติ (health check ผ่าน, network OK, ไม่มี error ใน logs ที่เกี่ยวกับ infra)
> ปัญหาน่าจะอยู่ที่ระดับ application/code ภายใน container อาจต้องดู:
> - Application logs ที่ละเอียดกว่า
> - Business logic / code ที่เกี่ยวข้อง
> - Configuration ของ application เอง


