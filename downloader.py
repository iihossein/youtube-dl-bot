import asyncio
import os
import uuid
import logging
import tempfile

import yt_dlp

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")


def _get_cookie_path() -> str | None:
    """اول از env می‌خواند، بعد از فایل لوکال."""
    cookies_content = os.getenv("YTDLP_COOKIES")
    if cookies_content:
        temp = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        )
        temp.write(cookies_content)
        temp.close()
        logger.info("Cookies loaded from YTDLP_COOKIES env var.")
        return temp.name

    local_cookies = os.path.join(BASE_DIR, "cookies.txt")
    if os.path.exists(local_cookies):
        logger.info("Cookies loaded from local cookies.txt file.")
        return local_cookies

    logger.warning("No cookies found (neither YTDLP_COOKIES nor cookies.txt)")
    return None


def _build_ydl_opts(
    output_template: str,
    format_spec: str,
    cookie_path: str | None,
) -> dict:
    """
    ساخت یک dict مشترک برای دو بار دانلود (ویدیو و صدا).

    نکات کلیدی:
    - player_client = "web" → با کوکی‌های معتبر کار می‌کند.
    - remote_components = ["ejs:github"] → چالش n را از راه دور حل می‌کند.
    - js_runtimes = {"node": {}} → از Node.js برای اجرای اسکریپت EJS استفاده می‌کند.
    """
    opts = {
        "format": format_spec,
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        # ✅ استفاده از کلاینت web که با کوکی سازگار است
        "extractor_args": {
            "youtube": {
                "player_client": ["web"],
            },
        },
        # ✅ حل چالش JavaScript از راه دور (EJS scripts)
        "remote_components": ["ejs:github"],
        # ✅ استفاده از Node.js برای اجرای اسکریپت EJS
        "js_runtimes": {"node": {}},
    }
    if cookie_path:
        opts["cookiefile"] = cookie_path
    return opts


def _download_sync(
    url: str,
    output_template: str,
    format_spec: str,
    cookie_path: str | None,
) -> None:
    opts = _build_ydl_opts(output_template, format_spec, cookie_path)
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def _find_file_by_prefix(prefix: str) -> str | None:
    """چون yt-dlp ممکن است پسوند را تغییر دهد، بر اساس prefix جستجو می‌کنیم."""
    for name in os.listdir(DOWNLOAD_DIR):
        if name.startswith(prefix):
            return os.path.join(DOWNLOAD_DIR, name)
    return None


async def download_video_and_audio(url: str) -> tuple[str, str]:
    """دانلود ویدیو و صدا به صورت جداگانه. مسیر دو فایل را برمی‌گرداند."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    uid = str(uuid.uuid4())

    video_template = os.path.join(DOWNLOAD_DIR, f"{uid}_video.%(ext)s")
    audio_template = os.path.join(DOWNLOAD_DIR, f"{uid}_audio.%(ext)s")

    cookie_path = _get_cookie_path()
    loop = asyncio.get_running_loop()

    try:
        # ---------- VIDEO ----------
        logger.info("Downloading video...")
        await loop.run_in_executor(
            None,
            _download_sync,
            url,
            video_template,
            "bestvideo[height<=480]/bestvideo[height<=720]/bestvideo",
            cookie_path,
        )
        video_path = _find_file_by_prefix(f"{uid}_video")
        if not video_path:
            raise RuntimeError("فایل ویدیو ساخته نشد.")

        # ---------- AUDIO ----------
        logger.info("Downloading audio...")
        await loop.run_in_executor(
            None,
            _download_sync,
            url,
            audio_template,
            "bestaudio/best",
            cookie_path,
        )
        audio_path = _find_file_by_prefix(f"{uid}_audio")
        if not audio_path:
            raise RuntimeError("فایل صدا ساخته نشد.")

        logger.info("Download complete: video=%s audio=%s", video_path, audio_path)
        return video_path, audio_path

    except Exception:
        for prefix in (f"{uid}_video", f"{uid}_audio"):
            p = _find_file_by_prefix(prefix)
            if p and os.path.exists(p):
                os.remove(p)
        raise
    finally:
        if cookie_path and cookie_path.startswith(tempfile.gettempdir()):
            if os.path.exists(cookie_path):
                os.remove(cookie_path)