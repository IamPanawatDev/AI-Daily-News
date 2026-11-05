import os
import json
import re
import logging
from datetime import datetime
import feedparser
import requests
from dotenv import load_dotenv

# โหลดค่าคอนฟิกจาก .env
load_dotenv()

# ตั้งค่า Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# แหล่งข่าว AI RSS Feeds (คัดสรรแหล่งข่าวชั้นนำ)
RSS_FEEDS = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    },
    {
        "name": "Google News (AI)",
        "url": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:1d&hl=en-US&gl=US&ceid=US:en",
    },
]


def clean_html(text):
    """ลบ HTML tags และช่องว่างส่วนเกินออกจากข้อความ"""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def fetch_latest_news(max_items=10):
    """ดึงข่าวล่าสุดจาก RSS Feeds และรวมรายการเข้าด้วยกัน"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles = []
    seen_urls = set()

    for feed_info in RSS_FEEDS:
        name = feed_info["name"]
        url = feed_info["url"]
        logging.info(f"กำลังดึงข่าวจาก: {name} ({url})")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:4]:
                link = getattr(entry, "link", "")
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                title = clean_html(getattr(entry, "title", "No Title"))
                summary_raw = getattr(entry, "summary", getattr(entry, "description", ""))
                summary = clean_html(summary_raw)[:200]

                articles.append(
                    {
                        "source": name,
                        "title": title,
                        "summary": summary,
                        "url": link,
                    }
                )
        except Exception as e:
            logging.warning(f"ไม่สามารถดึงข้อมูลจาก {name}: {e}")

    logging.info(f"รวบรวมข่าวได้ทั้งหมด {len(articles)} ข่าว")
    return articles[:max_items]


def summarize_with_gemini(articles):
    """ส่งรายการข่าวให้ Gemini สรุปภาษาไทยและจัดรูปแบบเป็น JSON"""
    if not GEMINI_API_KEY:
        raise ValueError("ไม่พบคีย์ GEMINI_API_KEY กรุณาตั้งค่าใน .env หรือ Secrets")

    prompt = f"""คุณคือ AI News Editor สรุปข่าว AI ในรอบวันสำหรับคนไทย
คัดเลือกข่าวที่สำคัญที่สุด 5 ข่าวจากรายการด้านล่าง แล้วสรุปเป็นภาษาไทยที่กระชับและเข้าใจง่าย

รายการข่าว:
{json.dumps(articles, ensure_ascii=False, indent=1)}

ตอบกลับเป็น JSON array เท่านั้น (ไม่มีคำเกริ่น ห้ามใส่ข้อความอื่นนอกเหนือจาก JSON):
[
  {{
    "title_th": "หัวข้อข่าวภาษาไทย",
    "summary_th": "สรุปเนื้อหาสำคัญ 2 ประโยค",
    "key_takeaway": "ประเด็นที่น่าจับตา 1 ประโยคสั้นๆ",
    "source_name": "ชื่อสำนักข่าว",
    "url": "ลิงก์ข่าว"
  }}
]"""

    # โมเดล Gemini ยอดนิยมที่มีในระบบ
    candidate_models = [
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]

    for model_name in candidate_models:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
            },
        }

        try:
            logging.info(f"กำลังเรียกใช้ Gemini API ด้วยโมเดล: {model_name}...")
            resp = requests.post(api_url, json=payload, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

                # ล้าง code block markdown หาก Gemini คืนมาใน ```json ... ```
                if "```" in raw_text:
                    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw_text, re.DOTALL)
                    if match:
                        raw_text = match.group(1).strip()
                    else:
                        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

                parsed_json = json.loads(raw_text)
                logging.info(f"Gemini สรุปข่าวสำเร็จ ({len(parsed_json)} ข่าว)")
                return parsed_json
            else:
                logging.warning(
                    f"โมเดล {model_name} คืนสถานะ {resp.status_code}: {resp.text[:150]}"
                )
        except Exception as e:
            logging.warning(f"เกิดข้อผิดพลาดกับโมเดล {model_name}: {e}")

    raise RuntimeError("ไม่สามารถสรุปข่าวด้วย Gemini API ได้ทุกโมเดลที่กำหนด")


def send_to_discord(news_items):
    """ส่งสรุปข่าวไปยัง Discord Webhook ในรูปแบบ Embeds ที่สวยงาม"""
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("ไม่พบ DISCORD_WEBHOOK_URL กรุณาตั้งค่าใน .env หรือ Secrets")

    today_str = datetime.now().strftime("%d/%m/%Y")
    
    # การ์ดหัวเรื่อง (Header Embed)
    embeds = [
        {
            "title": f"☀️ ข่าวเด่น AI ประจำวัน | {today_str}",
            "description": "สรุปประเด็นข่าวสารสำคัญในวงการปัญญาประดิษฐ์และเทคโนโลยีประจำเช้าวันนี้",
            "color": 0x5865F2,  # สี Blurple ของ Discord
            "footer": {
                "text": "AI Daily News • ขับเคลื่อนด้วย Google Gemini & GitHub Actions"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    ]

    # การ์ดสำหรับแต่ละข่าว (News Embeds)
    colors = [0x00A86B, 0x0088FF, 0xF4B400, 0xEA4335, 0x8E44AD]
    for idx, item in enumerate(news_items, start=1):
        color = colors[(idx - 1) % len(colors)]
        embeds.append(
            {
                "title": f"#{idx} {item.get('title_th', 'ข่าว AI ล่าสุด')}",
                "description": (
                    f"{item.get('summary_th', '')}\n\n"
                    f"💡 **จุดเด่น/ความสำคัญ:** {item.get('key_takeaway', '-')}\n"
                    f"📰 **ที่มา:** {item.get('source_name', 'ข่าวออนไลน์')} • [อ่านฉบับเต็ม]({item.get('url', '')})"
                ),
                "color": color,
            }
        )

    # ส่งเข้า Discord (Discord รับได้สูงสุด 10 embeds ต่อ 1 request)
    payload = {
        "username": "AI Daily News Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
        "embeds": embeds,
    }

    logging.info("กำลังส่งข้อความไปยัง Discord...")
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
    if resp.status_code in (200, 204):
        logging.info("✅ ส่งข่าวเข้า Discord เรียบร้อยแล้ว!")
    else:
        logging.error(f"❌ ส่งเข้า Discord ล้มเหลว: {resp.status_code} - {resp.text}")
        raise RuntimeError(f"Discord Webhook Failed: {resp.status_code}")


def main():
    logging.info("=== เริ่มต้นกระบวนการ AI Daily News ===")
    try:
        articles = fetch_latest_news()
        if not articles:
            logging.warning("ไม่พบข่าวจาก RSS Feeds ในรอบนี้")
            return

        summarized_news = summarize_with_gemini(articles)
        send_to_discord(summarized_news)
        logging.info("=== ทำงานเสร็จสมบูรณ์เรียบร้อย ===")
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการทำงาน: {e}", exc_info=True)
        # ส่งแจ้งเตือน error ไปยัง Discord ด้วยหากต้องการ
        try:
            if DISCORD_WEBHOOK_URL:
                requests.post(
                    DISCORD_WEBHOOK_URL,
                    json={
                        "content": f"⚠️ **AI Daily News Error**: เกิดข้อผิดพลาดระหว่างสรุปข่าว: `{str(e)}`"
                    },
                    timeout=10,
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()
