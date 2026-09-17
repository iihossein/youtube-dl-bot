import asyncio
import os
import uuid
import logging
import tempfile

import yt_dlp

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"

def _get_cookie_path() -> str | None:
    """Reads cookies from environment variable and writes to a temp file."""
    cookies_content = os.getenv("YTDLP_COOKIES")
    if not cookies_content:
        return None
    
    # Create a temporary file to store the cookies
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
    }
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def download_video(url: str) -> str:
    """دانلود ویدیو و برگرداندن مسیر فایل."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp4")

    cookie_path = _get_cookie_path()

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, _download_sync, url, output_path, cookie_path)
    finally:
        # Clean up the temporary cookie file
        if cookie_path and os.path.exists(cookie_path):
            os.remove(cookie_path)
            logger.info("Temporary cookie file removed.")

    if not os.path.exists(output_path):
        raise RuntimeError("فایل دانلود نشد")

    return output_path