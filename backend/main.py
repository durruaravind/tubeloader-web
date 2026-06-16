from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from downloader import download
from progress import progress

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str

latest_file = {"path": None}

@app.post("/download")
def start_download(req: DownloadRequest):
    progress["percent"] = 0
    file_path = download(req.url)
    latest_file["path"] = file_path
    return {"status": "completed"}

@app.get("/progress")
def get_progress():
    return progress

@app.get("/file")
def get_file():
    if latest_file["path"] and os.path.exists(latest_file["path"]):
        return FileResponse(
            latest_file["path"],
            media_type="video/mp4",
            filename=os.path.basename(latest_file["path"])
        )
    return {"error": "No file"}
