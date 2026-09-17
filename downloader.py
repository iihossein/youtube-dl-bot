import asyncio
import logging
import os
import tempfile
import uuid

import yt_dlp


logger = logging.getLogger(__name__)


DOWNLOAD_DIR = "downloads"

MAX_RETRIES = 3
RETRY_DELAY = 5

BGUTIL_SERVER_HOME = "/app/bgutil-ytdlp-pot-provider/server"


def _get_cookie_path() -> str | None:
    """
    Cookie ها را از Environment Variable می‌گیرد
    و داخل یک فایل موقت قرار می‌دهد.
    """

    cookies_content = os.getenv("YTDLP_COOKIES")

    if not cookies_content:
        return None

    temp_cookie_file = tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        suffix=".txt",
        encoding="utf-8",
    )

    try:
        temp_cookie_file.write(cookies_content)
        temp_cookie_file.close()

        logger.info("YouTube cookies loaded from environment.")

        return temp_cookie_file.name

    except Exception:
        temp_cookie_file.close()

        if os.path.exists(temp_cookie_file.name):
            os.remove(temp_cookie_file.name)

        raise


def _download_sync(
    url: str,
    output_path: str,
    cookie_path: str | None,
) -> None:

    ydl_opts = {
        # کیفیت مناسب برای ربات
        "format": "bestvideo*+bestaudio/best",

        # خروجی نهایی
        "merge_output_format": "mp4",

        # مسیر فایل
        "outtmpl": output_path,

        # لاگ کمتر
        "quiet": True,
        "no_warnings": True,

        # فقط همان ویدیو
        "noplaylist": True,

        # استفاده از EJS
        "remote_components": "ejs:github",

        # استفاده از Node برای JavaScript
        "js_runtimes": {
            "node": {},
        },

        # YouTube client
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb"],
            },

            # استفاده از bgutil در حالت Script
            "youtubepot-bgutilscript": {
                "server_home": BGUTIL_SERVER_HOME,
            },
        },
    }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


async def download_video(url: str) -> str:

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    output_path = os.path.join(
        DOWNLOAD_DIR,
        f"{uuid.uuid4()}.mp4",
    )

    cookie_path = _get_cookie_path()

    loop = asyncio.get_running_loop()

    try:

        for attempt in range(1, MAX_RETRIES + 1):

            try:
                logger.info(
                    f"Download attempt {attempt}/{MAX_RETRIES}: {url}"
                )

                # اگر از تلاش قبلی فایل ناقص باقی مانده باشد
                if os.path.exists(output_path):
                    os.remove(output_path)

                await loop.run_in_executor(
                    None,
                    _download_sync,
                    url,
                    output_path,
                    cookie_path,
                )

                if not os.path.exists(output_path):
                    raise RuntimeError(
                        "Download finished but output file was not found."
                    )

                logger.info(
                    f"Download successful on attempt {attempt}"
                )

                return output_path

            except Exception as e:

                logger.warning(
                    f"Download attempt {attempt} failed: {e}"
                )

                # پاک کردن فایل ناقص
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        logger.warning(
                            "Could not remove incomplete output file."
                        )

                if attempt == MAX_RETRIES:
                    logger.error(
                        "All download attempts failed."
                    )
                    raise

                await asyncio.sleep(RETRY_DELAY)

    finally:

        # Cookie موقت همیشه باید پاک شود
        if cookie_path and os.path.exists(cookie_path):
            try:
                os.remove(cookie_path)
                logger.info("Temporary cookie file removed.")
            except OSError:
                logger.warning(
                    "Could not remove temporary cookie file."
                )