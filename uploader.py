import os
import logging
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

async def upload_to_transfer_sh(file_path: str) -> str:
    """آپلود به transfer.sh"""
    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(f"آپلود {file_size_mb:.1f} MB...")
        
        with open(file_path, 'rb') as f:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://transfer.sh/',
                    data={'file': f},
                    timeout=aiohttp.ClientTimeout(total=3600)
                ) as resp:
                    if resp.status == 200:
                        download_url = (await resp.text()).strip()
                        logger.info(f"آپلود موفق: {download_url}")
                        return download_url
                    else:
                        logger.error(f"خطای آپلود: {resp.status}")
                        return None
    
    except Exception as e:
        logger.error(f"خطا در آپلود: {str(e)}")
        return None
