import os
import re
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

from config import MAX_FILE_SIZE_BYTES
from downloader import download_video_and_audio
from merger import merge_video_audio

logger = logging.getLogger(__name__)
router = Router()

YOUTUBE_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/watch\?v=[\w-]+"
    r"|youtu\.be/[\w-]+"
    r"|youtube\.com/shorts/[\w-]+)",
    re.IGNORECASE,
)


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "سلام 👋\n\n"
        "لینک YouTube را بفرست تا دانلودش کنم.\n"
        "⚠️ برای شروع، ویدیوهای کوتاه (زیر ۵ دقیقه) بهتر کار می‌کنند."
    )


@router.message(F.text)
async def youtube_handler(message: Message):
    match = YOUTUBE_PATTERN.search(message.text)
    if not match:
        await message.answer("لطفاً یک لینک معتبر YouTube ارسال کن.")
        return

    url = match.group(0)
    if not url.startswith("http"):
        url = "https://" + url

    status = await message.answer("⏳ شروع دانلود...")

    video_path = None
    audio_path = None
    final_path = None

    try:
        # ---------- DOWNLOAD ----------
        await status.edit_text("🎬 در حال دانلود ویدیو و صدا...")
        video_path, audio_path = await download_video_and_audio(url)

        # ---------- MERGE ----------
        await status.edit_text("🔧 در حال ادغام...")
        final_path = await merge_video_audio(video_path, audio_path)

        # پاک‌سازی فایل‌های میانی
        for p in (video_path, audio_path):
            if p and os.path.exists(p):
                os.remove(p)
        video_path = None
        audio_path = None

        # ---------- SIZE CHECK ----------
        file_size = os.path.getsize(final_path)
        size_mb = file_size / (1024 * 1024)

        if file_size > MAX_FILE_SIZE_BYTES:
            await status.edit_text(
                f"❌ حجم فایل {size_mb:.1f}MB است.\n"
                f"متأسفانه تلگرام فایل‌های بالای ۵۰MB را قبول نمی‌کند.\n"
                f"لطفاً ویدیوی کوتاه‌تری امتحان کن."
            )
            return

        # ---------- UPLOAD TO TELEGRAM ----------
        await status.edit_text(f"📤 در حال آپلود ({size_mb:.1f}MB)...")

        video_input = FSInputFile(final_path, filename="video.mp4")
        await message.answer_video(
            video_input,
            caption=f"✅ دانلود شد\n📦 حجم: {size_mb:.1f}MB",
            supports_streaming=True,
        )
        await status.delete()

    except Exception as error:
        logger.exception("Handler failed")
        await status.edit_text(
            f"❌ خطا:\n{type(error).__name__}: {str(error)[:500]}"
        )

    finally:
        for path in (video_path, audio_path, final_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass