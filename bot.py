import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)

from config import (
    BOT_TOKEN,
    USE_WEBHOOK,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    WEBAPP_HOST,
    WEBAPP_PORT,
)
from handlers import router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # ---------- ساخت ربات و دیسپچر ----------
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    # =====================================
    # حالت ۱: Polling (لوکال)
    # =====================================
    if not USE_WEBHOOK:
        logger.info("Starting bot in POLLING mode...")
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        finally:
            await bot.session.close()
        return

    # =====================================
    # حالت ۲: Webhook (Railway)
    # =====================================
    if not WEBHOOK_URL:
        raise ValueError(
            "USE_WEBHOOK=true است اما WEBHOOK_URL خالی است. "
            "WEBHOOK_HOST را در Variables تنظیم کن."
        )

    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook set to %s", WEBHOOK_URL)

    app = web.Application()

    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()

    logger.info("Server started on %s:%s", WEBAPP_HOST, WEBAPP_PORT)

    try:
        # اجرای دائمی تا زمانی که پروسه kill شود
        await asyncio.Event().wait()
    finally:
        # پاک‌سازی هنگام خروج
        await bot.delete_webhook()
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")