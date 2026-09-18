import re
import logging
import uuid
from aiogram import Router, types
from aiogram.filters import Command
from downloader import download_video, cleanup_old_files
from uploader import upload_to_transfer_sh

logger = logging.getLogger(__name__)
router = Router()

YOUTUBE_REGEX = r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/\S+"

@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 سلام!\n\n"
        "لطفاً لینک YouTube را ارسال کن.\n"
        "ربات ویدیو را دانلود کرده و برایت لینک دانلود می‌فرستد."
    )

@router.message()
async def handle_youtube_link(message: types.Message):
    """پردازش لینک YouTube"""
    
    # بررسی لینک
    if not re.search(YOUTUBE_REGEX, message.text):
        await message.answer("❌ لینک YouTube معتبر نیست!")
        return
    
    url = message.text.strip()
    video_id = str(uuid.uuid4())[:8]
    
    # پیام در حال پردازش
    status_msg = await message.answer("⏳ در حال دانلود...")
    
    try:
        logger.info(f"URL دریافت شد: {url} از کاربر {message.from_user.id}")
        
        # دانلود
        output_file = await download_video(url, video_id)
        if not output_file:
            await status_msg.edit_text("❌ خطا: نتوانستم ویدیو را دانلود کنم")
            return
        
        # آپلود
        await status_msg.edit_text("📤 در حال آپلود...")
        download_link = await upload_to_transfer_sh(output_file)
        
        if not download_link:
            await status_msg.edit_text("❌ خطا: نتوانستم فایل را آپلود کنم")
            return
        
        # پاسخ نهایی
        await status_msg.edit_text(
            f"✅ ویدیو آماده است!\n\n"
            f"📥 [دانلود کن]({download_link})\n\n"
            f"⏰ لینک تا ۲۴ ساعت معتبر است",
            parse_mode="Markdown"
        )
        
        # پاک‌کردن فایل‌های قدیمی
        await cleanup_old_files()
    
    except Exception as e:
        logger.error(f"خطا: {str(e)}")
        await status_msg.edit_text(f"❌ خطا: {str(e)}")
