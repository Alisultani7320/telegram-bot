import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دریافت توکن از متغیرهای محیطی
TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
MAILGUN_KEY = os.getenv("MAILGUN_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")

# وارد کردن کدهای اصلی بات
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import start, handle_text, handle_pdf

# ایجاد اپلیکیشن
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# تابع اصلی برای Vercel
async def handler(event, context):
    try:
        # بررسی درخواست POST از تلگرام
        if event["httpMethod"] == "POST":
            body = json.loads(event["body"])
            update = Update.de_json(body, application.bot)
            await application.process_update(update)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"status": "ok"})
            }
        # برای تست با GET
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": "Telegram Bot is running!"
        }
    except Exception as e:
        logging.error(f"خطا در پردازش درخواست: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/plain"},
            "body": str(e)
        }
