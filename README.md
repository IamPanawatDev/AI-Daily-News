# 🤖 AI-Daily-News

ระบบ AI สรุปข่าวสารวงการปัญญาประดิษฐ์ (AI) ส่งเข้า Discord อัตโนมัติทุกเที่ยงคืนเวลา 00:00 น. **ฟรี 100%** โดยไม่ต้องเปิดคอมพิวเตอร์ทิ้งไว้

---

## 🌟 จุดเด่นของโปรเจกต์
- 🆓 **ฟรี 100%:** ใช้บริการ Free Tier ทั้งหมด ไม่ต้องผูกบัตรเครดิต
- ☁️ **Serverless / Cloud Automation:** ทำงานอัตโนมัติผ่าน GitHub Actions ไม่เปลืองไฟ ไม่ต้องเปิดเครื่องคอมพิวเตอร์
- 📰 **แหล่งข่าวชั้นนำ:** ดึงข่าวอัปเดตจาก TechCrunch AI, The Verge, MIT Technology Review และ Google News
- 🧠 **Google Gemini AI:** คัดสรรและสรุปเนื้อหาเป็นภาษาไทยที่กระชับ สละสลวย เข้าใจง่าย
- 🎨 **Discord Embeds:** จัดรูปแบบข้อความสวยงาม แยกสีตามหัวข้อ พร้อมลิงก์ไปยังข่าวต้นฉบับ

---

## ⚙️ สถาปัตยกรรมการทำงาน (Architecture)

```text
[ GitHub Actions (Cron 08:00 AM น.) ]
                 │
                 ▼
     [ ดึงข่าวจาก RSS Feeds ]
(TechCrunch, The Verge, MIT, Google News)
                 │
                 ▼
       [ Google Gemini API ]
(วิเคราะห์ คัดเลือก 5 ข่าวเด่น & สรุปเป็นภาษาไทย)
                 │
                 ▼
       [ Discord Webhook ]
(ส่งการ์ดสรุปข่าวเข้าห้องแชต Discord สวยงาม)
```

---

## 🚀 การติดตั้งและทดสอบบนเครื่องตัวเอง (Local Run)

### 1. เตรียมความพร้อม
- ติดตั้ง Python 3.10 ขึ้นไป
- ติดตั้ง Dependencies:
```bash
pip install -r requirements.txt
```

### 2. ตั้งค่าคีย์ (.env)
คัดลอกไฟล์ `.env.example` เป็น `.env` แล้วระบุคีย์ของคุณ:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
```

### 3. รันสคริปต์
```bash
python main.py
```

---

## ⏰ การทำงานอัตโนมัติผ่าน GitHub Actions

โปรเจกต์นี้ตั้งค่า Workflow ไว้ที่ `.github/workflows/daily_news.yml`
- **ตารางเวลา:** ทำงานทุกวันเวลา `17:00 UTC` ซึ่งตรงกับ **เที่ยงคืน (00:00 น.) ตามเวลาประเทศไทย**
- **Trigger ด้วยตนเอง:** สามารถเข้าไปที่แท็บ **Actions** บน GitHub แล้วกดปุ่ม **Run workflow** เพื่อทดสอบให้บอทส่งข่าวทันทีได้ตลอดเวลา

### การตั้งค่า Repository Secrets บน GitHub
ไปที่ GitHub Repository ของคุณ:
1. ไปที่ **Settings** > **Secrets and variables** > **Actions**
2. เพิ่ม **Repository secrets** 2 ค่าดังนี้:
   - `GEMINI_API_KEY`: คีย์ Gemini API จาก Google AI Studio
   - `DISCORD_WEBHOOK_URL`: ลิงก์ Webhook URL ของ Discord Channel

---

## 📁 โครงสร้างโปรเจกต์
```text
AI-Daily-News/
├── .github/
│   └── workflows/
│       └── daily_news.yml    # GitHub Actions workflow สำหรับตั้งเวลา
├── .env.example              # ตัวอย่างไฟล์ Environment Variables
├── .gitignore                # ป้องกันการเผลออัปโหลด .env ขึ้น Git
├── main.py                   # โค้ดหลัก (ดึงข่าว -> สรุปด้วย Gemini -> ส่ง Discord)
├── requirements.txt          # รายการ Library ของ Python
└── README.md                 # เอกสารอธิบายการใช้งาน
```
