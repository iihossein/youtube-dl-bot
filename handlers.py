from pytubefix import YouTube
from pytubefix.cli import on_progress
import logging

logger = logging.getLogger(__name__)

async def extract_download_link(url: str) -> str:
    """استخراج لینک دانلود مستقیم از YouTube"""
    try:
        yt = YouTube(
            url,
            use_oauth=False,
            allow_oauth_cache=False
        )
        
        # دریافت بهترین stream موجود
        stream = yt.streams.filter(
            progressive=True,  # صدا + ویدیو در یک فایل
            file_extension='mp4'
        ).order_by('resolution').desc().first()
        
        if not stream:
            # اگر progressive موجود نبود
            stream = yt.streams.get_highest_resolution()
        
        if not stream:
            logger.error(f"No streams available for {url}")
            return "❌ خطا: هیچ فرمت قابل دسترس یافت نشد"
        
        logger.info(f"Stream URL extracted: {stream.url[:50]}...")
        return stream.url
    
    except Exception as e:
        logger.error(f"Error extracting URL: {str(e)}")
        return f"❌ خطا: {str(e)}"
