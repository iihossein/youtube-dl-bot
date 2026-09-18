import os
from dotenv import load_dotenv

load_dotenv()

# =====================================
# Telegram
# =====================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده است")

# =====================================
# Webhook
# =====================================
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", "8080"))

# =====================================
# Download limits
# =====================================
# حداکثر حجم فایل برای آپلود در تلگرام (50 MB)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024