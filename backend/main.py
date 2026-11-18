import os
import shutil
import subprocess
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import imageio_ffmpeg
import yt_dlp
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="TubeLoader API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tubeloader-web.vercel.app",
        "https://tubeloader-web-git-feature-stream-download-no-storage-aravind3d.vercel.app",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition"],
)

executor = ThreadPoolExecutor(max_workers=2)
tasks = {}
tasks_lock = threading.Lock()

POT_PROVIDER_VERSION = "2.0.2"
POT_PROVIDER_HOME = Path(tempfile.gettempdir()) / "bgutil-ytdlp-pot-provider"
POT_PROVIDER_SERVER = POT_PROVIDER_HOME / "server"


def setup_pot_provider():
    """Install the bgutil script provider once per Render instance."""
    if (POT_PROVIDER_SERVER / "src" / "generate_once.ts").is_file():
        return
    shutil.rmtree(POT_PROVIDER_HOME, ignore_errors=True)
    subprocess.run(
        [
            "git", "clone", "--depth", "1", "--single-branch",
            "--branch", POT_PROVIDER_VERSION,
            "https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git",
            str(POT_PROVIDER_HOME),
        ],
        check=True, capture_output=True, text=True, timeout=180,
    )
    subprocess.run(
        ["deno", "install", "--allow-scripts=npm:canvas", "--frozen"],
        cwd=str(POT_PROVIDER_SERVER),
        check=True, capture_output=True, text=True, timeout=360,
    )


@app.on_event("startup")
def initialize_youtube_support():
    try:
        setup_pot_provider()
        print(f"YouTube PO token script provider initialized: {POT_PROVIDER_SERVER / 'src' / 'generate_once.ts'}")
    except Exception as exc:
        # Keep the API available; yt-dlp may still work for videos that do not
        # require a PO token. The failure is visible in Render logs.
        print(f"WARNING: YouTube PO token provider setup failed: {exc}")


class VideoRequest(BaseModel):
    url: str
    quality: int | None = Field(default=720, ge=144, le=4320)


def validate_youtube_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()
    allowed = host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")
    if parsed.scheme not in ("http", "https") or not allowed:
        raise HTTPException(status_code=400, detail="Please enter a valid YouTube video URL.")
    return value.strip()


def ffmpeg_path():
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def metadata_options():
    options = {
        "quiet": True,
        "verbose": True,
        "no_warnings": False,
        "skip_download": True,
        "noplaylist": True,
        # Avoid the web_embedded client, which has recently caused player-response
        # extraction failures for some YouTube videos.
        "js_runtimes": {"deno": {}},
        "extractor_args": {
            "youtube": {"player_client": ["default", "-web_embedded"]},
            "youtubepot-bgutilscript": {"script_path": str(POT_PROVIDER_SERVER / "src" / "generate_once.ts")},
        },
    }
    binary = ffmpeg_path()
    if binary:
        options["ffmpeg_location"] = binary
    return options


def extract_video_info(url: str):
    try:
        with yt_dlp.YoutubeDL(metadata_options()) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read this video: {str(exc)[:240]}")
    if not info or info.get("_type") == "playlist":
        raise HTTPException(status_code=422, detail="Please use a single YouTube video URL, not a playlist.")
    heights = sorted({
        int(item["height"])
        for item in info.get("formats", [])
        if item.get("ext") == "mp4"
        and item.get("vcodec") != "none"
        and item.get("height")
        and int(item["height"]) <= 2160
    })
    return {
        "id": info.get("id"),
        "title": info.get("title") or "YouTube video",
        "channel": info.get("channel") or info.get("uploader") or "Unknown channel",
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "qualities": heights,
    }


@app.get("/")
def health():
    return {"status": "ok", "service": "TubeLoader API"}


@app.post("/api/info")
def get_info(request: VideoRequest):
    url = validate_youtube_url(request.url)
    return extract_video_info(url)


def progress_hook(task_id: str):
    def hook(data):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                raise yt_dlp.utils.DownloadError("Download task no longer exists.")
            cancel_event = task["cancel_event"]
        if cancel_event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")
        if data.get("status") == "downloading":
            downloaded = data.get("downloaded_bytes") or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            percent = round(downloaded * 100 / total, 1) if total else 0
            speed = data.get("speed")
            eta = data.get("eta")
            with tasks_lock:
                if task_id in tasks:
                    tasks[task_id].update({
                        "percent": percent,
                        "speed": speed,
                        "eta": eta,
                        "status": "downloading",
                    })
        elif data.get("status") == "finished":
            with tasks_lock:
                if task_id in tasks:
                    tasks[task_id]["percent"] = 100
                    tasks[task_id]["status"] = "processing"
    return hook


def expire_task(task_id: str):
    with tasks_lock:
        task = tasks.pop(task_id, None)
    if task and task.get("temp_dir"):
        shutil.rmtree(task["temp_dir"], ignore_errors=True)


def schedule_expiry(task_id: str, seconds: int):
    timer = threading.Timer(seconds, expire_task, args=(task_id,))
    timer.daemon = True
    timer.start()


def run_download(task_id: str, url: str, quality: int):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            return
        task["status"] = "starting"
    temp_dir = tempfile.mkdtemp(prefix="tubeloader_")
    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]["temp_dir"] = temp_dir
    try:
        binary = ffmpeg_path()
        format_selector = (
            f"best[ext=mp4][height<={quality}]/"
            f"bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/"
            "best[ext=mp4]"
        )
        options = {
            "format": format_selector,
            "outtmpl": os.path.join(temp_dir, "%(title).160B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "js_runtimes": {"deno": {}},
            "extractor_args": {
                "youtube": {"player_client": ["default", "-web_embedded"]},
                "youtubepot-bgutilscript": {"script_path": str(POT_PROVIDER_SERVER / "src" / "generate_once.ts")},
            },
            "no_warnings": True,
            "progress_hooks": [progress_hook(task_id)],
            "merge_output_format": "mp4",
            "retries": 3,
            "fragment_retries": 3,
        }
        if binary:
            options["ffmpeg_location"] = binary
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = Path(ydl.prepare_filename(info))
            if not filepath.exists():
                candidates = list(Path(temp_dir).glob("*.mp4"))
                if candidates:
                    filepath = candidates[0]
            if not filepath.exists():
                raise RuntimeError("The MP4 file was not created. Please try another quality.")
        with tasks_lock:
            task = tasks.get(task_id)
            if task and task["cancel_event"].is_set():
                raise yt_dlp.utils.DownloadError("Download cancelled by user.")
            if task:
                task.update({
                    "status": "completed",
                    "percent": 100,
                    "file_path": str(filepath),
                    "filename": filepath.name,
                })
        schedule_expiry(task_id, 900)
    except Exception as exc:
        cancelled = False
        with tasks_lock:
            task = tasks.get(task_id)
            if task:
                cancelled = task["cancel_event"].is_set()
                task.update({
                    "status": "cancelled" if cancelled else "error",
                    "error": "Download cancelled." if cancelled else str(exc)[:300],
                })
        shutil.rmtree(temp_dir, ignore_errors=True)
        schedule_expiry(task_id, 60)


@app.post("/api/download")
def start_download(request: VideoRequest):
    url = validate_youtube_url(request.url)
    if not request.quality:
        raise HTTPException(status_code=400, detail="Choose a video quality.")
    task_id = str(uuid.uuid4())
    with tasks_lock:
        tasks[task_id] = {
            "status": "queued",
            "percent": 0,
            "speed": None,
            "eta": None,
            "error": None,
            "filename": None,
            "file_path": None,
            "temp_dir": None,
            "cancel_event": threading.Event(),
        }
    executor.submit(run_download, task_id, url, request.quality)
    return {"task_id": task_id}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Download task not found or expired.")
        return {
            "status": task["status"],
            "percent": task["percent"],
            "speed": task["speed"],
            "eta": task["eta"],
            "error": task["error"],
            "filename": task["filename"],
        }


@app.post("/api/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Download task not found.")
        if task["status"] in ("completed", "error", "cancelled"):
            return {"status": task["status"]}
        task["cancel_event"].set()
        task["status"] = "cancelling"
    return {"status": "cancelling"}


def cleanup_task(task_id: str, temp_dir: str):
    shutil.rmtree(temp_dir, ignore_errors=True)
    with tasks_lock:
        tasks.pop(task_id, None)


@app.get("/api/tasks/{task_id}/file")
def download_file(task_id: str, background_tasks: BackgroundTasks):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task or task["status"] != "completed" or not task["file_path"]:
            raise HTTPException(status_code=409, detail="The video is not ready yet.")
        filepath = task["file_path"]
        temp_dir = task["temp_dir"]
        filename = task["filename"]
    if not filepath or not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="The temporary video file has expired.")
    background_tasks.add_task(cleanup_task, task_id, temp_dir)
    return FileResponse(
        filepath,
        media_type="video/mp4",
        filename=filename,
        headers={"Cache-Control": "no-store"},
        background=background_tasks,
    )
