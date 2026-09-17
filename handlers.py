from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "سلام! 👋\n\n"
        "لینک ویدیوی YouTube را برای من بفرست تا دانلودش کنم."
    )