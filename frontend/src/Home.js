import { useEffect, useMemo, useRef, useState } from "react";
import "./Home.css";

const API = (process.env.REACT_APP_API || "http://localhost:8000").replace(/\/$/, "");
const HISTORY_KEY = "tubeloader_history";

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return "—";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins >= 60
    ? `${Math.floor(mins / 60)}h ${mins % 60}m`
    : `${mins}m ${secs}s`;
}

function formatSpeed(bytesPerSecond) {
  if (!Number.isFinite(bytesPerSecond) || bytesPerSecond <= 0) return "—";
  const mb = bytesPerSecond / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB/s` : `${(bytesPerSecond / 1024).toFixed(0)} KB/s`;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [video, setVideo] = useState(null);
  const [quality, setQuality] = useState(720);
  const [taskId, setTaskId] = useState(null);
  const [task, setTask] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); }
    catch { return []; }
  });
  const [showHistory, setShowHistory] = useState(false);
  const autoStarted = useRef(false);

  const qualities = useMemo(() => {
    const available = (video?.qualities || []).filter((height) => height <= 2160);
    return [...new Set(available)].sort((a, b) => a - b);
  }, [video]);

  useEffect(() => {
    if (!taskId) return undefined;
    let active = true;
    const poll = async () => {
      try {
        const response = await fetch(`${API}/api/tasks/${taskId}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Unable to check download status.");
        if (!active) return;
        setTask(data);
        if (data.status === "completed" && !autoStarted.current) {
          autoStarted.current = true;
          const item = {
            id: taskId,
            title: video?.title || "YouTube video",
            channel: video?.channel || "Unknown channel",
            thumbnail: video?.thumbnail || "",
            quality,
            duration: video?.duration || null,
            downloadedAt: new Date().toISOString(),
          };
          setHistory((current) => {
            const next = [item, ...current.filter((entry) => entry.id !== taskId)].slice(0, 30);
            localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
            return next;
          });
          window.location.assign(`${API}/api/tasks/${taskId}/file`);
          setBusy(false);
        } else if (["error", "cancelled"].includes(data.status)) {
          setBusy(false);
          if (data.status === "error") setError(data.error || "Download failed.");
          setTaskId(null);
        }
      } catch (err) {
        if (active) {
          setError(err.message);
          setBusy(false);
          setTaskId(null);
        }
      }
    };
    poll();
    const timer = window.setInterval(poll, 1000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [taskId, video, quality]);

  const inspectVideo = async () => {
    setError("");
    setVideo(null);
    setTask(null);
    setLoadingInfo(true);
    try {
      const response = await fetch(`${API}/api/info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), quality: 720 }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load video details.");
      setVideo(data);
      const available = (data.qualities || []).filter((height) => height <= 2160);
      setQuality(available.includes(720) ? 720 : (available[available.length - 1] || 360));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingInfo(false);
    }
  };

  const startDownload = async () => {
    setError("");
    setBusy(true);
    setTask({ status: "queued", percent: 0, speed: null, eta: null });
    autoStarted.current = false;
    try {
      const response = await fetch(`${API}/api/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), quality }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not start download.");
      setTaskId(data.task_id);
    } catch (err) {
      setError(err.message);
      setBusy(false);
      setTask(null);
    }
  };

  const cancelDownload = async () => {
    if (!taskId) return;
    try {
      await fetch(`${API}/api/tasks/${taskId}/cancel`, { method: "POST" });
      setTask((current) => ({ ...current, status: "cancelling" }));
    } catch (err) {
      setError("Could not cancel this download. Please try again.");
    }
  };

  const reset = () => {
    setUrl("");
    setVideo(null);
    setTask(null);
    setTaskId(null);
    setError("");
    setBusy(false);
  };

  const progress = Math.max(0, Math.min(100, Number(task?.percent) || 0));

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" onClick={(event) => { event.preventDefault(); setShowHistory(false); }}>
          <span className="brand-mark">T</span> TubeLoader
        </a>
        <button className="history-toggle" onClick={() => setShowHistory((value) => !value)}>
          {showHistory ? "Back to downloader" : `Download history (${history.length})`}
        </button>
      </header>

      {showHistory ? (
        <section className="history-panel">
          <div className="eyebrow">YOUR RECENT DOWNLOADS</div>
          <h1>Download history</h1>
          <p className="muted">History is saved in this browser only. It contains video details, not downloaded files or file locations.</p>
          {history.length === 0 ? <div className="empty-state">Your completed downloads will appear here.</div> : (
            <div className="history-list">
              {history.map((item) => (
                <article className="history-item" key={item.id}>
                  {item.thumbnail ? <img src={item.thumbnail} alt="" /> : <div className="thumb-placeholder">▶</div>}
                  <div className="history-copy">
                    <strong>{item.title}</strong>
                    <span>{item.channel} · {item.quality}p · {new Date(item.downloadedAt).toLocaleString()}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
          {history.length > 0 && <button className="text-button" onClick={() => {
            localStorage.removeItem(HISTORY_KEY);
            setHistory([]);
          }}>Clear browser history</button>}
        </section>
      ) : (
        <section className="hero-card">
          <div className="eyebrow">SIMPLE. FAST. MP4.</div>
          <h1>YouTube Video<br /><span>Downloading Tool</span></h1>
          <p className="intro">Save videos you own or are authorized to download. Choose a quality and download the MP4 directly through your browser.</p>

          <label className="field-label" htmlFor="video-url">YouTube video URL</label>
          <div className="url-row">
            <input id="video-url" value={url} onChange={(event) => setUrl(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter" && !busy && !loadingInfo) inspectVideo(); }}
              placeholder="https://www.youtube.com/watch?v=..." disabled={busy} />
            <button className="inspect-button" onClick={inspectVideo} disabled={busy || loadingInfo || !url.trim()}>
              {loadingInfo ? "Checking…" : "Fetch video"}
            </button>
          </div>

          {error && <div className="error-message" role="alert">{error}</div>}

          {video && (
            <div className="video-preview">
              {video.thumbnail && <img className="video-thumbnail" src={video.thumbnail} alt="Video thumbnail" />}
              <div className="video-details">
                <h2>{video.title}</h2>
                <p>{video.channel} <span>·</span> {formatDuration(video.duration)}</p>
                <label className="field-label quality-label" htmlFor="quality">Video quality</label>
                <select id="quality" value={quality} onChange={(event) => setQuality(Number(event.target.value))} disabled={busy}>
                  {qualities.map((height) => <option key={height} value={height}>{height}p</option>)}
                </select>
              </div>
            </div>
          )}

          {busy && task && (
            <div className="progress-panel">
              <div className="progress-heading">
                <strong>{task.status === "cancelling" ? "Cancelling…" : task.status === "processing" ? "Preparing MP4…" : "Downloading…"}</strong>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
              <div className="progress-meta">
                <span>Speed: {formatSpeed(task.speed)}</span>
                <span>ETA: {Number.isFinite(task.eta) ? formatDuration(task.eta) : "Calculating…"}</span>
              </div>
              <button className="cancel-button" onClick={cancelDownload} disabled={task.status === "cancelling"}>
                {task.status === "cancelling" ? "Cancelling download" : "Cancel download"}
              </button>
            </div>
          )}

          {!busy && video && (
            <button className="download-button" onClick={startDownload}>Download MP4 <span>↓</span></button>
          )}
          {!busy && !video && <div className="hint">Paste a video link above, then fetch its details to continue.</div>}
          <div className="privacy-note"><span>⌁</span> No account. No database. Temporary server files are deleted after delivery.</div>
        </section>
      )}
      <footer>TubeLoader · MP4 downloads only</footer>
    </main>
  );
}
