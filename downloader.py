import os
import logging
import asyncio
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = "/tmp/youtube_downloads"
Path(DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)

async def download_video(url: str, video_id: str) -> str:
    """دانلود ویدیو با yt-dlp (ویدیو + صوت ادغام شده)"""
    try:
        logger.info(f"شروع دانلود: {url}")
        
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp4")
        
        # دستور yt-dlp
        cmd = [
            'yt-dlp',
            '-f', 'best[ext=mp4]',  # بهترین فرمت MP4
            '-o', output_path,
            '--quiet',
            url
        ]
        
        # اجرای yt-dlp به صورت غیر‌همزمان
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        if process.returncode != 0:
            logger.error(f"yt-dlp خطا: {stderr.decode()}")
            return None
        
        if os.path.exists(output_path):
            file_size_mb = os.path.getsize(output_path) / 1024 / 1024
            logger.info(f"دانلود موفق: {file_size_mb:.1f} MB")
            return output_path
        else:
            logger.error("فایل دانلود شده یافت نشد")
            return None
    
    except asyncio.TimeoutError:
        logger.error("تایم‌آوت دانلود")
        return None
    except Exception as e:
        logger.error(f"خطا در دانلود: {str(e)}")
        return None

async def cleanup_old_files(max_age_seconds=3600):
    """حذف فایل‌های قدیمی‌تر از 1 ساعت"""
    import time
    current_time = time.time()
    try:
        for file in Path(DOWNLOADS_DIR).glob("*.mp4"):
            if current_time - file.stat().st_mtime > max_age_seconds:
                file.unlink()
                logger.info(f"حذف فایل قدیمی: {file}")
    except Exception as e:
        logger.error(f"خطا در پاک‌کردن: {str(e)}")
