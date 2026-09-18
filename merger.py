import asyncio
import os
import subprocess
import uuid
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")


def _merge_sync(video_path: str, audio_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",       # اولین جریان ویدیو از ورودی اول
        "-map", "1:a:0",       # اولین جریان صدا از ورودی دوم
        "-c:v", "copy",        # کپی ویدیو بدون re-encode (سریع)
        "-c:a", "aac",         # تبدیل صدا به aac (سازگار با تلگرام)
        "-b:a", "128k",
        "-movflags", "+faststart",  # برای پخش سریع در تلگرام
        output_path,
    ]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("ffmpeg merge failed:\n" + result.stderr[-2000:])


async def merge_video_audio(video_path: str, audio_path: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}_final.mp4")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, _merge_sync, video_path, audio_path, output_path
    )
    if not os.path.exists(output_path):
        raise RuntimeError("فایل نهایی توسط ffmpeg ساخته نشد.")
    return output_path