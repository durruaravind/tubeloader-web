import { useEffect, useState } from "react";

const API = process.env.REACT_APP_API;

export default function Home() {
  const [url, setUrl] = useState("");
  const [progress, setProgress] = useState(0);

  const download = async (fmt) => {
    await fetch(`${API}/download`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: url,
        fmt: fmt,
      }),
    });
  };

  useEffect(() => {
    const t = setInterval(() => {
      fetch(`${API}/progress`)
        .then(r => r.json())
        .then(d => setProgress(d.percent));
    }, 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen flex justify-center items-center bg-slate-100 p-4">
      <div className="w-full max-w-lg bg-white p-6 rounded-xl shadow">
        <h1 className="text-2xl font-bold text-center mb-4">
          YouTube Downloader
        </h1>

        <input
          className="w-full p-2 border rounded mb-4"
          placeholder="Paste YouTube URL"
          onChange={e => setUrl(e.target.value)}
        />

        <div className="flex gap-3 flex-col sm:flex-row">
          <button
            className="flex-1 bg-blue-500 text-white py-2 rounded"
            onClick={() => download("mp3")}
          >
            MP3
          </button>
          <button
            className="flex-1 bg-green-500 text-white py-2 rounded"
            onClick={() => download("mp4")}
          >
            MP4
          </button>
        </div>

        <div className="mt-5 bg-gray-200 rounded h-4">
          <div
            className="bg-green-500 h-4 rounded"
            style={{ width: `${progress}%` }}
          />
        </div>

        <p className="text-center mt-2">{progress}%</p>
      </div>
    </div>
  );
}
