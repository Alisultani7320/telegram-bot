import os
import logging
import json
from telegram import Update
from telegram.ext import ContextTypes
import requests
from pdfminer.high_level import extract_text
import sqlite3
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دریافت کلیدهای API از متغیرهای محیطی
TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
MAILGUN_KEY = os.getenv("MAILGUN_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")

# مسیر دیتابیس
DB_PATH = '/tmp/calendar.db'

# راه‌اندازی دیتابیس SQLite
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event TEXT NOT NULL,
        date TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# راه‌اندازی اولیه دیتابیس
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات آماده‌ست! بگو: چت، تصویر، تقویم، ایمیل یا PDF")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if "تصویر" in text:
        await update.message.reply_text("در حال تولید تصویر... لطفاً صبر کنید.")
        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": text}
            )
            
            if response.status_code == 200:
                await update.message.reply_photo(response.content)
            else:
                await update.message.reply_text(f"خطا در تولید تصویر: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"خطا در تولید تصویر: {str(e)}")
    
    elif "تقویم" in text:
        parts = text.split("تقویم", 1)
        if len(parts) > 1:
            event_text = parts[1].strip()
            if event_text:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO events (user_id, event, date) VALUES (?, ?, date('now'))",
                        (update.effective_user.id, event_text)
                    )
                    conn.commit()
                    conn.close()
                    await update.message.reply_text("رویداد با موفقیت ذخیره شد!")
                except Exception as e:
                    await update.message.reply_text(f"خطا در ذخیره رویداد: {str(e)}")
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT event, date FROM events WHERE user_id = ? ORDER BY date DESC LIMIT 5",
                        (update.effective_user.id,)
                    )
                    events = cursor.fetchall()
                    conn.close()
                    
                    if events:
                        events_text = "رویدادهای اخیر شما:\n\n"
                        for event, date in events:
                            events_text += f"📅 {date}: {event}\n"
                        await update.message.reply_text(events_text)
                    else:
                        await update.message.reply_text("شما هیچ رویدادی ندارید.")
                except Exception as e:
                    await update.message.reply_text(f"خطا در بازیابی رویدادها: {str(e)}")
    
    elif "ایمیل" in text:
        parts = text.split("ایمیل", 1)
        if len(parts) > 1:
            email_text = parts[1].strip()
            if email_text:
                try:
                    # تجزیه ساده برای قسمت‌های ایمیل
                    email_parts = email_text.split("|")
                    if len(email_parts) >= 3:
                        to_email = email_parts[0].strip()
                        subject = email_parts[1].strip()
                        body = email_parts[2].strip()
                        
                        response = requests.post(
                            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                            auth=("api", MAILGUN_KEY),
                            data={
                                "from": f"Telegram Bot <mailgun@{MAILGUN_DOMAIN}>",
                                "to": to_email,
                                "subject": subject,
                                "text": body
                            }
                        )
                        
                        if response.status_code == 200:
                            await update.message.reply_text("ایمیل با موفقیت ارسال شد!")
                        else:
                            await update.message.reply_text(f"خطا در ارسال ایمیل: {response.text}")
                    else:
                        await update.message.reply_text("فرمت نادرست. لطفاً به این صورت وارد کنید: ایمیل example@example.com | موضوع | متن پیام")
                except Exception as e:
                    await update.message.reply_text(f"خطا در ارسال ایمیل: {str(e)}")
            else:
                await update.message.reply_text("برای ارسال ایمیل، لطفاً به این صورت وارد کنید: ایمیل example@example.com | موضوع | متن پیام")
    
    else:
        # پیش‌فرض به چت با Mistral
        await update.message.reply_text("در حال پردازش پیام شما... لطفاً صبر کنید.")
        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": text}
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    # استخراج متن تولید شده
                    generated_text = result[0].get("generated_text", "")
                    # محدود کردن طول پاسخ
                    if len(generated_text) > 4000:
                        generated_text = generated_text[:4000] + "..."
                    await update.message.reply_text(generated_text)
                else:
                    await update.message.reply_text("متأسفانه نتوانستم پاسخی تولید کنم. لطفاً دوباره تلاش کنید.")
            else:
                await update.message.reply_text(f"خطا در دریافت پاسخ: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"خطا در پردازش پیام: {str(e)}")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("در حال دریافت و تحلیل PDF... لطفاً صبر کنید.")
    
    try:
        # دریافت فایل از تلگرام
        file = await update.message.document.get_file()
        file_path = f"/tmp/{update.message.document.file_name}"
        await file.download_to_drive(file_path)
        
        # استخراج متن از PDF
        text = extract_text(file_path)
        
        # محدود کردن طول متن برای پاسخ
        if len(text) > 4000:
            text_preview = text[:4000] + "..."
        else:
            text_preview = text
        
        await update.message.reply_text(f"متن استخراج شده از PDF:\n\n{text_preview}")
        
        # پاکسازی
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"خطا در تحلیل PDF: {str(e)}")

