import asyncio
import os
import uuid
import logging
import tempfile

import yt_dlp

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"

# حداکثر تعداد تلاش مجدد
MAX_RETRIES = 3
# تأخیر بین تلاش‌ها (به ثانیه)
RETRY_DELAY = 5


def _get_cookie_path() -> str | None:
    """خواندن کوکی‌ها از متغیر محیطی و نوشتن در یک فایل موقت."""
    cookies_content = os.getenv("YTDLP_COOKIES")
    if not cookies_content:
        return None

    temp_cookie_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.txt', encoding='utf-8'
    )
    temp_cookie_file.write(cookies_content)
    temp_cookie_file.close()
    logger.info("Cookies loaded from environment variable into a temp file.")
    return temp_cookie_file.name


def _download_sync(url: str, output_path: str, cookie_path: str | None) -> None:
    """اجرای sync دانلود (داخل thread جداگانه اجرا می‌شود)."""
    ydl_opts = {
        "format": "best[ext=mp4][height<=360]/best[height<=360]/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # افزودن گزینه remote-components برای سازگاری با YouTube
        "remote_components": "ejs:github",
    }
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


async def download_video(url: str) -> str:
    """دانلود ویدیو با قابلیت تلاش مجدد در صورت خطای موقت."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp4")

    cookie_path = _get_cookie_path()

    loop = asyncio.get_event_loop()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Download attempt {attempt} for {url}")
            await loop.run_in_executor(None, _download_sync, url, output_path, cookie_path)
            
            if os.path.exists(output_path):
                logger.info(f"Download successful on attempt {attempt}")
                break
            else:
                raise RuntimeError("File not found after download")

        except Exception as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt == MAX_RETRIES:
                logger.error("All download attempts failed.")
                raise
            # صبر قبل از تلاش مجدد
            await asyncio.sleep(RETRY_DELAY)
        finally:
            # پاک‌سازی فایل کوکی فقط پس از پایان همه تلاش‌ها
            if attempt == MAX_RETRIES and cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)
                logger.info("Temporary cookie file removed.")

    return output_path