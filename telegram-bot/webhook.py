import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دریافت توکن از متغیرهای محیطی
TOKEN = os.getenv("TELEGRAM_TOKEN")

# وارد کردن کدهای اصلی بات
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import start, handle_text, handle_pdf

# ایجاد اپلیکیشن
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# تابع اصلی برای Vercel
def handler(event, context):
    try:
        # بررسی درخواست POST از تلگرام
        if event["httpMethod"] == "POST":
            body = json.loads(event["body"])
            update = Update.de_json(body, application.bot)
            if update:
                application.run_async(application.process_update(update))
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"status": "ok"})
                }
            else:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Invalid update"})
                }
        # برای تست با GET
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Telegram Bot is running!"})
        }
    except Exception as e:
        logging.error(f"Error in handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/plain"},
            "body": str(e)
        }
