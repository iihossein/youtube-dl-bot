import os
import re
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from downloader import download_video

logger = logging.getLogger(__name__)
router = Router()

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)\S+"
)


def is_youtube_link(message: Message) -> bool:
    """فیلتر سفارشی: آیا پیام حاوی لینک YouTube است؟"""
    if not message.text:
        return False
    return bool(YOUTUBE_REGEX.search(message.text))


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "سلام! 👋\n\n"
        "لینک ویدیوی YouTube را برای من بفرست تا دانلودش کنم."
    )


@router.message(is_youtube_link)
async def handle_youtube_link(message: Message):
    url_match = YOUTUBE_REGEX.search(message.text)
    url = url_match.group(0)
    logger.info(f"Received URL: {url} from user {message.from_user.id}")

    status_msg = await message.answer("⏳ در حال دانلود...")

    try:
        file_path = await download_video(url)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        await status_msg.edit_text(
            f"✅ دانلود شد\n"
            f"📦 حجم: {size_mb:.2f} MB\n"
            f"📁 فایل: {os.path.basename(file_path)}"
        )
    except Exception as e:
        logger.exception("Download failed")
        await status_msg.edit_text(f"❌ خطا در دانلود:\n{type(e).__name__}: {e}")