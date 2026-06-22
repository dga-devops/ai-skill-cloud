# Steerings — ชุดไฟล์ตั้งค่า AI สำหรับเอาไปใช้ซ้ำ (พกพาได้ ใช้ได้ทุกคน)

ชุดสำเร็จรูปของไฟล์สั่งงาน AI (steering / instructions) + ระบบความจำที่เก็บลง Obsidian vault
ของผู้ใช้แต่ละคน ก็อปไปวางในโปรเจกต์ไหน เครื่องใครก็ได้ ให้ AI (Kiro, VSCode Copilot, Claude Code)
ทำงานแนวเดียวกันทุกที่ **ไม่มี path เฉพาะเครื่องฮาร์ดโค้ดอยู่เลย**

แก้ 2 ปัญหา:
1. AI เดาคำสั่ง shell ผิดเวลาอ่านไฟล์นอก workspace → เปลือง credit
2. ความจำของงานหาย → เขียนลงวอลต์ของผู้ใช้โดยตรง AI แก้ index เองได้ ไม่ต้องลาก ไม่ต้องสคริปต์

---

## วิธีติดตั้ง (Quick Start)

1. **ก็อปไฟล์ในชุดนี้ไปไว้ที่ root ของโปรเจกต์ปลายทาง** (เอาเฉพาะเครื่องมือที่ใช้ก็ได้ — ดูตารางหัวข้อ "เอาไปวางตรงไหน")
   ขั้นต่ำสุด: โฟลเดอร์ steering ของเครื่องมือนั้น + `vault-template.md` (+ `.gitignore`)

   ตัวอย่างก็อปทั้งชุดด้วย PowerShell (รวมโฟลเดอร์ที่ขึ้นต้นด้วยจุด):
   ```powershell
   Copy-Item -Path '<ที่อยู่ steerings>\*' -Destination '<โปรเจกต์ปลายทาง>' -Recurse -Force
   ```

2. **เปิดโปรเจกต์ปลายทางด้วย AI** (Kiro / Copilot agent mode / Claude Code)
   - Kiro โหลด `.kiro/steering/*.md` อัตโนมัติ
   - Copilot ต้องเปิด setting `github.copilot.chat.codeGeneration.useInstructionFiles`

3. **คุยทำงานตามปกติ** พองานแรกที่ "ควรจด" เกิดขึ้น AI จะหา `.memory-vault` / `~/.memory-vault` ไม่เจอ
   → **ถาม path วอลต์ของคุณ** ตอบ path เต็มของโฟลเดอร์ Knowledge ไป (เช่น `D:\Obsidian Vault\Knowledge`)

4. AI เก็บ path ลง `~/.memory-vault` (ครั้งเดียวต่อเครื่อง), scaffold วอลต์ถ้ายังว่าง, แล้วเขียน entry + แก้ index ให้เอง

> ครั้งต่อๆ ไปบนเครื่องเดิมไม่ถาม path ซ้ำ เพราะอ่านจาก `~/.memory-vault` ได้เลย

---

## โครงไฟล์ในชุดนี้

```
steerings/
├─ .kiro/steering/                         # Kiro (แยกไฟล์ native)
│  ├─ shell-and-file-reading.md
│  └─ memory-capture.md
├─ .github/instructions/                   # Copilot (แยกไฟล์ scoped ด้วย applyTo)
│  ├─ shell-and-file-reading.instructions.md
│  └─ memory-capture.instructions.md
├─ AGENTS.md                               # โปรโตคอลกลาง (shell + memory)
├─ CLAUDE.md                               # Claude Code (import AGENTS.md)
├─ vault-template.md                       # โครงสร้าง + format ของวอลต์ (seed → _system/)
├─ knowledge-vault.md                      # สรุปวิธี maintain วอลต์ สำหรับคน (seed → _system/)
├─ .gitignore                              # กัน .memory-vault หลุดขึ้น git
└─ README.md
```

ตอนใช้งานจริงจะมีไฟล์เพิ่มอัตโนมัติ: `.memory-vault` ที่ root (เก็บ path วอลต์ของเครื่องนั้น, ไม่ commit)

---

## เอาไปวางตรงไหนในโปรเจกต์จริง

| ในชุดนี้ | วางที่ (repo ปลายทาง) | ใครอ่าน |
| --- | --- | --- |
| `.kiro/steering/*.md` | `.kiro/steering/` | Kiro |
| `.github/instructions/*.instructions.md` | `.github/instructions/` | VSCode Copilot |
| `CLAUDE.md` | root | Claude Code |
| `AGENTS.md` | root | Claude Code + agent อื่นๆ |
| `vault-template.md` | root | ทุกตัว (ตอน scaffold/อ้างอิง format) |
| `knowledge-vault.md` | root | seed สำหรับ `_system/` (เอกสารให้คนอ่าน) |
| `.gitignore` | root (merge เข้าของเดิม) | git |

ก็อปทุกอย่างใน `steerings/` (รวมโฟลเดอร์ที่ขึ้นต้นด้วยจุด) ไปวางที่ root ของโปรเจกต์ปลายทางได้เลย

---

## เงื่อนไขของแต่ละเครื่องมือ

**Kiro** — `.kiro/steering/*.md` มี `inclusion: always` โหลดทุกแชต / user-global ที่ `~/.kiro/`

**VSCode Copilot** — `.github/instructions/*.instructions.md` ใช้กลไก 2 แบบ เลือกตามลักษณะงาน:
- `applyTo: '**'` = แนบเข้า context เมื่อมีไฟล์ถูกแก้ไข — ใช้กับ shell rules (ต้องรู้ตอนแตะไฟล์)
- `description` = agent ค้นเจอ on-demand เมื่องานตรงกับ description — ใช้กับ memory-capture (trigger หลังทำงานเสร็จ ไม่ใช่ตอนแก้ไฟล์)
- ใช้ทั้งคู่ได้ในไฟล์เดียวกัน (shell rules ใส่ทั้ง `applyTo` + `description` เพื่อให้ติดทั้งสองเส้นทาง)

⚠️ ระวัง: `description` ต้องเป็น quoted string บรรทัดเดียว (`"..."`) ห้ามใช้ YAML block `>` เพราะ colon ในเนื้อหาจะถูกตีว่าเป็น key ใหม่

ต้องเปิด setting `github.copilot.chat.codeGeneration.useInstructionFiles` และใช้ผ่าน Copilot Chat **Agent mode** เท่านั้น (inline/Ask mode ไม่อ่าน instruction)

**Claude Code** — อ่าน `CLAUDE.md` ที่ root ใช้ `@AGENTS.md` ดึงโปรโตคอลกลาง / user-global ที่ `~/.claude/CLAUDE.md`

---

## ระบบความจำ — เขียนลงวอลต์ของผู้ใช้โดยตรง

แนวคิด: ความจำอยู่ใน **Obsidian vault ของผู้ใช้** (ใช้ร่วมข้ามทุกโปรเจกต์) ไม่ได้อยู่ใน repo
เพราะ AI เป็นคนเขียนเอง มันเลย **แก้ index ในวอลต์ได้ inline** (อ่าน index เดิม + เติมแถว + เขียนกลับ)
ไม่มีปัญหา merge ไม่ต้องลากไฟล์ ไม่ต้องรันสคริปต์

### Init (ครั้งแรก / เครื่องใหม่) — AI จะถาม path เอง
- path วอลต์หาตามลำดับ: (1) `.memory-vault` ที่ root → (2) `~/.memory-vault` (ระดับเครื่อง)
- ถ้าไม่มีทั้งคู่ = ครั้งแรก → AI **ถามผู้ใช้** แล้วเก็บลง `~/.memory-vault` (ตั้งครั้งเดียว ใช้ทุกโปรเจกต์บนเครื่องนั้น ไม่โดนถามซ้ำ)
- ถ้าวอลต์ยังว่าง/ไม่มีโครง → AI scaffold จาก `vault-template.md` แล้วก็อปไปไว้ที่ `<vault>/_system/vault-template.md` เป็นเอกสารอ้างอิงของวอลต์เอง
- จะไม่เขียนจนกว่าจะรู้ path และผู้ใช้ยืนยัน

### หลัง init
- วอลต์อยู่นอก workspace → AI ใช้ shell อ่าน/เขียน บังคับ `-Encoding UTF8` ทุกครั้ง (entry มี `❌` ที่เป็น non-ASCII)
- บทเรียน → `<vault>/insights/{slug}.md` · error → `<vault>/errors/{slug}.md` · งานเฉพาะโปรเจกต์ → `<vault>/projects/{repo}/...`
- กฎ: อังกฤษเท่านั้น, lowercase-kebab ≤50 ตัว, ไม่มี date prefix, slug ห้ามซ้ำ (ซ้ำให้เติมคำต่อท้าย), ไม่จดงานจิ๊บจ๊อย
- แก้ index inline: errors → append แถวต่อท้าย `errors/index.md` (`Add-Content`, ปลอดภัยเพราะเป็นตารางล้วน) · insights → insert แถวใน Recent Insights ของ `index.md` (read-modify-write รักษา section อื่น)

> กฎปฏิบัติการอยู่ครบใน steering แล้ว AI ไม่ต้องอ่านวอลต์ทุกครั้งที่จด (ประหยัด credit) วอลต์ `_system/` ไว้เป็น seed ตอน init + อ้างอิงสำหรับคน

> ทำไม instruction ไม่ใช้ hook: hook รันทุกครั้งกินอีก 1 เทิร์น = เปลือง credit ให้ AI จดตอนจบงานไม่เสียเทิร์นเพิ่ม

---

## การดูแลรักษา

- กฎ shell อยู่ 3 ที่ (`.kiro/steering/`, `.github/instructions/`, `AGENTS.md`) เพราะแต่ละเครื่องมืออ่านแค่ไฟล์ตัวเอง **แก้แล้วต้อง sync ทั้ง 3** (`CLAUDE.md` ไม่นับ เพราะ import จาก `AGENTS.md`)
- memory-capture ก็อยู่ 3 ที่ด้วยเหตุผลเดียวกัน
- steering เขียนอังกฤษเพราะ `inclusion: always` โหลดทุกเทิร์น tokenize ประหยัดกว่าไทย ส่วน README นี้ (คนอ่าน) เป็นไทย
- Copilot instruction ใช้ `description` เป็น quoted string บรรทัดเดียวเสมอ ห้ามใช้ YAML block `>` (colon ในเนื้อหาจะถูกตีว่าเป็น key ใหม่ทำให้ error)
