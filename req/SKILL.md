---
name: req
description: จัดการ requirements ใน tasks.md — "req add" เพิ่ม req ใหม่, "req list" สรุปงานค้าง, "req do" ทำ task ถัดไป
---

# Skill: Requirement Management

จัดการ requirements ใน `tasks.md` — รองรับ 3 commands:

## Commands

### `req add <description>`
เพิ่ม requirement ใหม่

**Flow:**
1. วิเคราะห์ input → สรุปใจความ → ถามยืนยันก่อนเสมอ
2. รอผู้ใช้ confirm
3. เมื่อยืนยัน:
   - อ่าน `tasks.md` หา REQ number ถัดไป
   - ตรวจ codebase ว่ามี implementation แล้วหรือยัง
   - วิเคราะห์ dependency กับ REQ อื่น
   - เขียนต่อท้าย `tasks.md` ตาม format
   - เพิ่มรายการใน `## Requirements`
   - อัพเดท `## Dependency Graph` ถ้ามีความสัมพันธ์

### `req list`
แสดงสรุปงานที่ต้องทำ

**Flow:**
1. อ่าน `tasks.md`
2. แสดง Requirements checklist (เสร็จ/ยังไม่เสร็จ)
3. แสดง CDK tasks ที่ยังค้าง (เฉพาะ `- [ ]`)
4. แสดง dependency ที่ block อยู่
5. แสดง items ที่ต้อง clarify

### `req do`
ดำเนินการ task ถัดไป

**Flow:**
1. อ่าน `tasks.md` หา task แรกที่ยังไม่เสร็จ (`- [ ]`) จาก REQ ที่ไม่ถูก block โดย dependency
2. แสดงว่าจะทำ task อะไร → ถามยืนยัน
3. เมื่อยืนยัน → ดำเนินการ (สร้างไฟล์, แก้ code, run test ฯลฯ)
4. เมื่อเสร็จ → tick `- [x]` ใน `tasks.md`

---

## Format สำหรับ REQ ใหม่

```markdown
---

## REQ-N: <ชื่อสั้นกระชับ>

> บันทึก: YYYY-MM-DD

**Requirement:** <รายละเอียด>

**สถานะ:** ❌ ยังไม่ implement / ⚠️ implement บางส่วน

### CDK Tasks

- [ ] <task — ระบุไฟล์>
- [ ] Build & Test
- [ ] Deploy (`cdk deploy`)

### AWS Resources

- <resource ที่เกี่ยวข้อง>

### Dependencies (ถ้ามี)

- <dependency>

### ต้อง Clarify (ถ้ามี)

- <คำถาม>
```

เพิ่มใน Requirements section:
```
- [ ] REQ-N: <ชื่อ>
```
