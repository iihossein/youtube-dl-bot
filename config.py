import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
PORT = int(os.getenv("PORT", "8080"))

# مسیرهای دانلود
DOWNLOADS_DIR = "/tmp/youtube_downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# سرویس آپلود (اختیاری - بعداً تنظیم کنیم)
UPLOAD_SERVICE = os.getenv("UPLOAD_SERVICE", "transfer.sh")  # یا filebin.net
