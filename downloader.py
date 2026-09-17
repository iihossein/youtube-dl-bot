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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BGUTIL_SERVER_HOME = os.path.join(
    BASE_DIR,
    "bgutil-ytdlp-pot-provider",
    "server",
)


def _get_cookie_path() -> str | None:
    """
    Cookie ها را از Environment Variable می‌گیرد
    و داخل یک فایل موقت قرار می‌دهد.
    """

    cookies_content = os.getenv("YTDLP_COOKIES")

    if not cookies_content:
        logger.warning(
            "YTDLP_COOKIES is not configured."
        )
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

        logger.info(
            "YouTube cookies loaded from environment."
        )

        return temp_cookie_file.name

    except Exception:

        try:
            temp_cookie_file.close()
        except Exception:
            pass

        if os.path.exists(temp_cookie_file.name):
            os.remove(temp_cookie_file.name)

        raise


def _check_bgutil() -> None:
    """
    بررسی می‌کند که bgutil واقعاً در Deployment نصب شده باشد.
    """

    script_path = os.path.join(
        BGUTIL_SERVER_HOME,
        "build",
        "generate_once.js",
    )

    if not os.path.isfile(script_path):

        raise RuntimeError(
            "bgutil script not found.\n"
            f"Expected path: {script_path}\n"
            f"Server home: {BGUTIL_SERVER_HOME}"
        )

    logger.info(
        "bgutil script found: %s",
        script_path,
    )


def _download_sync(
    url: str,
    output_path: str,
    cookie_path: str | None,
) -> None:

    _check_bgutil()

    ydl_opts = {

        # بهترین کیفیت موجود
        "format": "bestvideo*+bestaudio/best",

        # خروجی نهایی MP4
        "merge_output_format": "mp4",

        # مسیر فایل
        "outtmpl": output_path,

        # لاگ کامل برای تشخیص مشکل
        "quiet": False,
        "no_warnings": False,

        # فقط همان ویدیو
        "noplaylist": True,

        # JavaScript components
        "remote_components": "ejs:github",

        # Node.js runtime
        "js_runtimes": {
            "node": {},
        },

        "extractor_args": {

            "youtube": {
                "player_client": [
                    "mweb",
                ],
            },

            # bgutil Script Mode
            "youtubepot-bgutilscript": {
                "server_home": BGUTIL_SERVER_HOME,
            },
        },
    }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    logger.info(
        "Using bgutil server home: %s",
        BGUTIL_SERVER_HOME,
    )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        ydl.download([url])


async def download_video(url: str) -> str:

    os.makedirs(
        DOWNLOAD_DIR,
        exist_ok=True,
    )

    output_path = os.path.join(
        DOWNLOAD_DIR,
        f"{uuid.uuid4()}.mp4",
    )

    cookie_path = _get_cookie_path()

    loop = asyncio.get_running_loop()

    try:

        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):

            try:

                logger.info(
                    "Download attempt %s/%s: %s",
                    attempt,
                    MAX_RETRIES,
                    url,
                )

                # حذف فایل ناقص قبلی
                if os.path.exists(output_path):

                    os.remove(output_path)

                await loop.run_in_executor(
                    None,
                    _download_sync,
                    url,
                    output_path,
                    cookie_path,
                )

                if not os.path.isfile(output_path):

                    raise RuntimeError(
                        "Download completed but "
                        "output file was not created."
                    )

                file_size = os.path.getsize(
                    output_path
                )

                if file_size <= 0:

                    raise RuntimeError(
                        "Downloaded file is empty."
                    )

                logger.info(
                    "Download successful. "
                    "Size=%s bytes",
                    file_size,
                )

                return output_path

            except Exception as e:

                logger.warning(
                    "Download attempt %s failed: %s",
                    attempt,
                    e,
                )

                if os.path.exists(output_path):

                    try:
                        os.remove(output_path)

                    except OSError:

                        logger.warning(
                            "Could not remove "
                            "incomplete output file."
                        )

                if attempt == MAX_RETRIES:

                    logger.error(
                        "All download attempts failed."
                    )

                    raise

                await asyncio.sleep(
                    RETRY_DELAY
                )

    finally:

        # Cookie موقت همیشه حذف شود
        if (
            cookie_path
            and os.path.exists(cookie_path)
        ):

            try:

                os.remove(cookie_path)

                logger.info(
                    "Temporary cookie file removed."
                )

            except OSError:

                logger.warning(
                    "Could not remove "
                    "temporary cookie file."
                ) 