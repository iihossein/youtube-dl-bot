import asyncio
import os
import uuid
import logging

import yt_dlp

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"


def _download_sync(url: str, output_path: str) -> None:
    """اجرای sync دانلود (داخل thread جداگانه اجرا می‌شود)."""
    ydl_opts = {
        "format": "best[ext=mp4][height<=360]/best[height<=360]/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


async def download_video(url: str) -> str:
    """دانلود ویدیو و برگرداندن مسیر فایل."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp4")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _download_sync, url, output_path)

    if not os.path.exists(output_path):
        raise RuntimeError("فایل دانلود نشد")

    return output_path