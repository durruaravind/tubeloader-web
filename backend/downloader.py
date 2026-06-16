import yt_dlp
import os
from progress import hook

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download(url):
    opts = {
        "format": "best[ext=mp4]",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "progress_hooks": [hook]
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename
