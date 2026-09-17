import re
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from pytubefix import YouTube

logger = logging.getLogger(__name__)
router = Router()

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)\S+"
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """دستور /start"""
    await message.answer(
        "سلام! 👋\n\n"
        "لینک ویدیوی YouTube را برای من بفرست "
        "تا لینک دانلود برات تولید کنم."
    )


@router.message(lambda msg: msg.text and YOUTUBE_REGEX.search(msg.text))
async def handle_youtube_link(message: Message):
    """دریافت لینک YouTube و تولید لینک دانلود"""
    
    # استخراج لینک
    url = YOUTUBE_REGEX.search(message.text).group(0)
    logger.info(f"URL received: {url} from user {message.from_user.id}")

    # پیام منتظر
    status_msg = await message.answer("⏳ در حال پردازش...")

    try:
        # بارگذاری ویدیو
        yt = YouTube(url)
        
        # انتخاب بهترین کیفیت دسترس‌پذیر
        stream = (
            yt.streams
            .filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )
        
        if not stream:
            await status_msg.edit_text(
                "❌ خطا: هیچ فرمت قابل دسترس یافت نشد"
            )
            return
        
        # دریافت اطلاعات
        title = yt.title or "ویدیو"
        resolution = stream.resolution or "نامشخص"
        download_url = stream.url
        
        # ارسال لینک دانلود
        await status_msg.edit_text(
            f"✅ آماده است!\n\n"
            f"<b>عنوان:</b> {title}\n"
            f"<b>کیفیت:</b> {resolution}\n\n"
            f"<a href='{download_url}'>کلیک برای دانلود</a>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.exception("Error occurred")
        error_msg = str(e)[:100]  # فقط ۱۰۰ کاراکتر اول
        await status_msg.edit_text(
            f"❌ خطا:\n<code>{error_msg}</code>",
            parse_mode="HTML"
        )
