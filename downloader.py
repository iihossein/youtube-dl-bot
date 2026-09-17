import asyncio
import logging
import os
import shutil
import tempfile
import uuid

import yt_dlp


logger = logging.getLogger(__name__)


DOWNLOAD_DIR = "downloads"

MAX_RETRIES = 3
RETRY_DELAY = 5


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BGUTIL_SCRIPT_PATH = os.path.join(
    BASE_DIR,
    "bgutil-ytdlp-pot-provider",
    "server",
    "build",
    "generate_once.js",
)


def _get_cookie_path() -> str | None:
    """
    Cookie ها را از Environment Variable می‌گیرد
    و داخل یک فایل موقت قرار می‌دهد.
    """

    cookies_content = os.getenv("YTDLP_COOKIES")

    if not cookies_content:
        logger.warning("YTDLP_COOKIES is not configured.")
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
        try:
            temp_cookie_file.close()
        except Exception:
            pass

        if os.path.exists(temp_cookie_file.name):
            os.remove(temp_cookie_file.name)

        raise


def _check_bgutil() -> None:
    """
    بررسی می‌کند که Provider و Node واقعاً
    داخل Deployment موجود باشند.
    """

    if not os.path.isfile(BGUTIL_SCRIPT_PATH):
        raise RuntimeError(
            "bgutil script not found: "
            f"{BGUTIL_SCRIPT_PATH}"
        )

    node_path = shutil.which("node")

    if not node_path:
        raise RuntimeError(
            "Node.js executable was not found in PATH."
        )

    logger.info(
        "bgutil script found: %s",
        BGUTIL_SCRIPT_PATH,
    )

    logger.info(
        "Node.js found: %s",
        node_path,
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

        # خروجی نهایی
        "merge_output_format": "mp4",

        # مسیر ذخیره
        "outtmpl": output_path,

        # برای این مرحله لاگ را خاموش نمی‌کنیم
        # تا وضعیت PO Token در Railway قابل مشاهده باشد.
        "quiet": False,
        "no_warnings": False,

        # فقط همان ویدیو
        "noplaylist": True,

        # EJS
        "remote_components": "ejs:github",

        # Node runtime
        "js_runtimes": {
            "node": {},
        },

        "extractor_args": {
            "youtube": {
                "player_client": ["mweb"],
            },

            # bgutil Script Mode
            "youtubepot-bgutilscript": {
                "script_path": BGUTIL_SCRIPT_PATH,
            },
        },
    }

    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    logger.info(
        "Using YouTube player client: mweb"
    )

    logger.info(
        "Using bgutil script: %s",
        BGUTIL_SCRIPT_PATH,
    )

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
                    "Download attempt %s/%s: %s",
                    attempt,
                    MAX_RETRIES,
                    url,
                )

                # حذف فایل احتمالی از تلاش قبلی
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
                        "Download completed but output file "
                        "was not created."
                    )

                file_size = os.path.getsize(output_path)

                if file_size <= 0:
                    raise RuntimeError(
                        "Downloaded file is empty."
                    )

                logger.info(
                    "Download successful. "
                    "Path=%s Size=%s bytes",
                    output_path,
                    file_size,
                )

                return output_path

            except Exception as e:

                logger.warning(
                    "Download attempt %s failed: %s",
                    attempt,
                    e,
                )

                # حذف فایل ناقص
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        logger.warning(
                            "Could not remove incomplete file: %s",
                            output_path,
                        )

                if attempt == MAX_RETRIES:
                    logger.error(
                        "All %s download attempts failed.",
                        MAX_RETRIES,
                    )
                    raise

                await asyncio.sleep(RETRY_DELAY)

    finally:

        # Cookie موقت همیشه حذف شود
        if cookie_path and os.path.exists(cookie_path):
            try:
                os.remove(cookie_path)

                logger.info(
                    "Temporary cookie file removed."
                )

            except OSError:
                logger.warning(
                    "Could not remove temporary cookie file."
                )