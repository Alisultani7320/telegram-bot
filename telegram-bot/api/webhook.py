from http.server import BaseHTTPRequestHandler
import json
import os
import logging
from telegram import Update
from telegram.ext import Application
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
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import start, handle_text, handle_pdf

# ایجاد و تنظیم اپلیکیشن
def setup_application():
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app

# تابع اصلی برای Vercel
async def handler(request):
    """تابع اصلی برای Vercel"""
    # ایجاد اپلیکیشن
    application = setup_application()
    
    if request.method == "POST":
        # بررسی مسیر وبهوک
        if request.url.path == f"/{TOKEN}":
            try:
                # دریافت و پردازش داده‌های JSON
                body = await request.json()
                
                # تبدیل به آبجکت Update
                update = Update.de_json(body, application.bot)
                
                # پردازش آپدیت
                await application.process_update(update)
                
                # ارسال پاسخ
                return {
                    "statusCode": 200,
                    "body": json.dumps({"status": "ok"}),
                }
            except Exception as e:
                logging.error(f"خطا در پردازش درخواست: {str(e)}")
                return {
                    "statusCode": 500,
                    "body": str(e),
                }
        else:
            return {
                "statusCode": 404,
                "body": "Not found",
            }
    else:
        return {
            "statusCode": 200,
            "body": "Telegram Bot is running!",
        }

