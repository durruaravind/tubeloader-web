import { useState } from "react";
import "./App.css";

const API_URL = process.env.REACT_APP_API || "http://127.0.0.1:8000";

export default function App() {
  const [url, setUrl] = useState("");
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);

  const startDownload = async () => {
    if (!url.includes("youtube.com") && !url.includes("youtu.be")) {
      alert("Enter a valid YouTube URL");
      return;
    }

    try {
      setLoading(true);
      setProgress(0);

      await fetch(`${API_URL}/download`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      const interval = setInterval(async () => {
        const res = await fetch(`${API_URL}/progress`);
        const data = await res.json();

        setProgress(data.percent);

        if (data.percent >= 100) {
          clearInterval(interval);
          setLoading(false);
          window.location.href = `${API_URL}/file`;
        }
      }, 1000);
    } catch (err) {
      setLoading(false);
      alert("Download failed");
    }
  };

  return (
    <div className="app">
      <div className="card">
        <h1>YouTube Video Downloading Tool</h1>
        <p>Download YouTube videos in MP4 format</p>

        <input
          type="text"
          placeholder="Paste YouTube URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <button onClick={startDownload} disabled={loading}>
          {loading ? "Downloading..." : "Download Video"}
        </button>

        <div className="progress-box">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          <span>{Math.floor(progress)}%</span>
        </div>
      </div>
    </div>
  );
}
