import json
import os
import logging

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تابع اصلی برای Vercel
def handler(event, context):
    try:
        # برای تست ساده، فقط یه پیام JSON برگردون
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Hello from Vercel! This is the webhook."})
        }
    except Exception as e:
        logging.error(f"Error in handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/plain"},
            "body": str(e)
        }
