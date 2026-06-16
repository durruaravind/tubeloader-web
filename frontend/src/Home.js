import { useEffect, useState } from "react";

const API = process.env.REACT_APP_API;

export default function Home() {
  const [url, setUrl] = useState("");
  const [progress, setProgress] = useState(0);
  const [downloading, setDownloading] = useState(false);

  const download = async () => {
    if (!url) return;

    const response = await fetch(`${API}/download`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: url,
      }),
    });

    const data = await response.json();
    console.log(data);

    if (response.ok) {
      window.location.href = `${API}/file`;
    }
  };

  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API}/progress`);
        const data = await res.json();

        if (typeof data.percent === "number") {
          setProgress(data.percent);
        }
      } catch (err) {
        console.error(err);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#007FFF",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "20px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "600px",
          background: "white",
          padding: "30px",
          borderRadius: "12px",
        }}
      >
        <h1
          style={{
            textAlign: "center",
            marginBottom: "20px",
          }}
        >
          YouTube Video Downloading Tool
        </h1>

        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste YouTube URL"
          style={{
            width: "100%",
            padding: "12px",
            marginBottom: "20px",
          }}
        />

        <button
          onClick={download}
          disabled={downloading}
          style={{
            width: "100%",
            padding: "12px",
            background: "red",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Download MP4
        </button>

        <div
          style={{
            marginTop: "20px",
            background: "#ddd",
            height: "20px",
            borderRadius: "10px",
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: "100%",
              background: "red",
              borderRadius: "10px",
            }}
          />
        </div>

        <p style={{ textAlign: "center", marginTop: "10px" }}>
          {progress}%
        </p>
      </div>
    </div>
  );
}