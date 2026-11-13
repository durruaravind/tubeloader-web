# TubeLoader

TubeLoader is a browser-based MP4 downloader UI backed by a FastAPI + yt-dlp service.

## Features

- YouTube video metadata preview (title, channel, thumbnail and duration)
- MP4 quality selection up to 2160p when available
- Live progress, transfer speed and ETA
- Per-task cancellation
- Browser-initiated MP4 download
- Browser-local history containing video metadata only
- Temporary server-side working directory; files are removed after delivery or expiry
- No database and no permanent download archive

## Architecture

`frontend/` is a Create React App project intended for Vercel.
`backend/` is a FastAPI service intended for Render.

The backend writes each active job to a unique temporary directory. The directory is removed after the response is sent, or after a 15-minute expiry if the browser never requests the completed file. Failed/cancelled jobs are cleaned up and their task records expire shortly afterwards. Task state is held in process memory only; this is not a durable queue and is intended for a single Render service instance.

## Deploy backend to Render

Create a Python web service from this repository and set:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/`

If you use a custom frontend domain, add its exact origin to the `allow_origins` list in `backend/main.py` (and redeploy). The production Vercel origin currently allowed is `https://tubeloader-web.vercel.app`.

The service installs an FFmpeg binary through `imageio-ffmpeg` for MP4 merging. Keep the Render instance and its temporary disk capacity in mind: concurrent video downloads consume temporary disk space.

## Deploy frontend to Vercel

Import the repository and set:

- Root Directory: `frontend`
- Framework Preset: Create React App
- Build Command: `npm run build`
- Output Directory: `build`
- Environment Variable: `REACT_APP_API=https://YOUR-RENDER-SERVICE.onrender.com`

The frontend environment variable must be set before building/redeploying. Do not include a trailing slash.

For local frontend development, copy `frontend/.env.example` to `frontend/.env` and set the API URL to `http://localhost:8000`.

## Run locally

Backend:

```bash
cd backend
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend, in another terminal:

```bash
cd frontend
npm install
npm start
```

## Important browser behavior

The backend cannot write directly into a visitor's `C:\\Downloads` directory. It sends the completed MP4 as an attachment; the browser saves it using the user's download settings. To use `C:\\Downloads`, set that folder as the browser's download location.

History is stored in the browser's local storage and contains only title, channel, thumbnail URL, quality, duration and completion time. It does not store a server file path or the downloaded video.

Only download videos you own or are authorized to download, and follow applicable copyright law and YouTube's terms.
