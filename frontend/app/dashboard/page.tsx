"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Job = {
  stage: string;
  progress: number;
  error: string | null;
  kind?: string;
};

type Project = {
  id: string;
  title: string;
  source_url: string;
  source_type: string;
  duration_sec: number;
  status: string;
  created_at: string;
  stage?: string | null;
  progress?: number | null;
  job?: Job | null;
  moments_count?: number;
};

type Hook = { text: string; rank: number };
type ClipRef = { id: string; status: string; export_path?: string | null };
type Moment = {
  id: string;
  start_sec: number;
  end_sec: number;
  score: number;
  score_reason: string;
  signals: Record<string, number>;
  hooks: Hook[];
  clips: ClipRef[];
};

type Credits = {
  plan: string;
  credits: number;
  plan_minutes: number;
};

function fmtTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

function stageLabel(stage?: string | null) {
  switch (stage) {
    case "queued":
      return "Queued";
    case "downloading":
      return "Downloading VOD";
    case "transcribing":
      return "Transcribing";
    case "detecting":
      return "Finding moments";
    case "ranking":
      return "Ranking clips";
    case "rendering":
      return "Rendering 9:16 MP4";
    case "ready":
      return "Ready";
    case "failed":
      return "Failed";
    default:
      return stage || "Working";
  }
}

function DashboardInner() {
  const search = useSearchParams();
  const [credits, setCredits] = useState<Credits | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(
    search.get("project")
  );
  const [project, setProject] = useState<Project | null>(null);
  const [moments, setMoments] = useState<Moment[]>([]);
  const [apiDown, setApiDown] = useState(false);
  const [url, setUrl] = useState("");
  const [submitMsg, setSubmitMsg] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // Per-moment review state: chosen hook index, custom hook text, clip job.
  const [hookChoice, setHookChoice] = useState<Record<string, number>>({});
  const [customHook, setCustomHook] = useState<Record<string, string>>({});
  const [clipState, setClipState] = useState<
    Record<string, { clipId: string; status: string; stage: string }>
  >({});
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadCredits = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/me/credits`);
      if (!r.ok) throw new Error();
      setCredits(await r.json());
      setApiDown(false);
    } catch {
      setApiDown(true);
    }
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/projects`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      setProjects(d.projects || []);
    } catch {
      setApiDown(true);
    }
  }, []);

  const loadProject = useCallback(async (id: string) => {
    try {
      const r = await fetch(`${API_URL}/api/projects/${id}`);
      if (!r.ok) throw new Error();
      const d: Project = await r.json();
      setProject(d);
      if (d.status === "ready") {
        const m = await fetch(`${API_URL}/api/projects/${id}/moments`);
        if (m.ok) {
          const md = await m.json();
          setMoments(md.moments || []);
        }
      }
    } catch {
      setApiDown(true);
    }
  }, []);

  // Initial load.
  useEffect(() => {
    loadCredits();
    loadProjects();
  }, [loadCredits, loadProjects]);

  // Poll the selected project while its job is still running.
  useEffect(() => {
    if (!selectedId) {
      setProject(null);
      setMoments([]);
      return;
    }
    loadProject(selectedId);
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => {
      loadProject(selectedId);
    }, 3000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [selectedId, loadProject]);

  // Stop polling once the project is ready (moments loaded) — the
  // interval above keeps refreshing, so just let it run cheaply; the
  // worker answers from SQLite. Poll clip renders separately below.

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    if (submitting || !url.trim()) return;
    setSubmitting(true);
    setSubmitMsg(null);
    try {
      const r = await fetch(`${API_URL}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      const d = await r.json().catch(() => null);
      if (!r.ok) {
        setSubmitMsg(
          (typeof d?.detail === "string" ? d.detail : null) ||
            "Could not start that VOD. Check the link and try again."
        );
        return;
      }
      setUrl("");
      setSubmitMsg(
        `Started: ${d.title} — ${d.credits_spent} credits for ${Math.ceil(
          d.duration_sec / 60
        )} minutes.`
      );
      setSelectedId(d.project_id);
      loadProjects();
      loadCredits();
    } catch {
      setSubmitMsg(
        "Could not reach the Hookclip worker. Is the API running?"
      );
    } finally {
      setSubmitting(false);
    }
  }

  function chosenHook(m: Moment): string {
    const i = hookChoice[m.id] ?? 0;
    if (customHook[m.id] !== undefined && customHook[m.id].trim() !== "") {
      return customHook[m.id].trim();
    }
    return m.hooks[i]?.text || "";
  }

  async function makeClip(m: Moment) {
    const hook = chosenHook(m);
    try {
      const r = await fetch(`${API_URL}/api/clips`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ moment_id: m.id, hook_text: hook }),
      });
      const d = await r.json().catch(() => null);
      if (!r.ok) {
        setSubmitMsg(
          (typeof d?.detail === "string" ? d.detail : null) ||
            "Could not create the clip."
        );
        return;
      }
      await exportClip(d.clip_id, m.id);
    } catch {
      setSubmitMsg("Could not reach the worker. Try again.");
    }
  }

  async function exportClip(clipId: string, momentId: string) {
    setClipState((s) => ({
      ...s,
      [momentId]: { clipId, status: "rendering", stage: "queued" },
    }));
    try {
      await fetch(`${API_URL}/api/clips/${clipId}/export`, {
        method: "POST",
      });
      // Poll until exported.
      const t = setInterval(async () => {
        try {
          const r = await fetch(`${API_URL}/api/clips/${clipId}`);
          if (!r.ok) return;
          const d = await r.json();
          setClipState((s) => ({
            ...s,
            [momentId]: {
              clipId,
              status: d.status,
              stage: d.job?.stage || d.status,
            },
          }));
          if (d.status === "exported" || d.status === "failed") {
            clearInterval(t);
            if (selectedId) loadProject(selectedId);
          }
        } catch {
          /* keep polling */
        }
      }, 3000);
    } catch {
      setClipState((s) => ({
        ...s,
        [momentId]: { clipId, status: "failed", stage: "failed" },
      }));
    }
  }

  const jobRunning =
    project &&
    project.job &&
    !["ready", "failed"].includes(project.job.stage);

  return (
    <div className="dash">
      <header className="site-header">
        <div className="wrap">
          <a className="logo" href="/">
            <span className="logo-mark">▶</span> Hookclip
          </a>
          <nav className="nav">
            <a href="/">Home</a>
            <a href="/dashboard">Dashboard</a>
          </nav>
          {credits && (
            <span className="credits-pill">
              {credits.plan} · {credits.credits} min left
            </span>
          )}
        </div>
      </header>

      <main className="wrap dash-main">
        <h1>Dashboard</h1>
        {apiDown && (
          <p className="dash-alert" role="alert">
            Can&rsquo;t reach the Hookclip worker at {API_URL}. The landing
            page and waitlist still work — the dashboard needs the worker
            API running.
          </p>
        )}

        <section className="dash-card">
          <h2>New project</h2>
          <p className="dash-sub">
            Paste a Twitch VOD or YouTube link. 1 credit = 1 source minute.
          </p>
          <form onSubmit={createProject} className="dash-form">
            <input
              type="url"
              required
              placeholder="https://www.twitch.tv/videos/… or youtube.com/watch?v=…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={submitting}
            />
            <button type="submit" className="btn btn-accent" disabled={submitting}>
              {submitting ? "Starting…" : "Find the clips"}
            </button>
          </form>
          {submitMsg && <p className="dash-note">{submitMsg}</p>}
        </section>

        <section className="dash-layout">
          <div className="dash-card">
            <h2>Your projects</h2>
            {projects.length === 0 ? (
              <p className="dash-sub">
                No projects yet. Paste a VOD link above to start your first
                one.
              </p>
            ) : (
              <ul className="proj-list">
                {projects.map((p) => (
                  <li key={p.id}>
                    <button
                      className={
                        "proj-item" + (p.id === selectedId ? " active" : "")
                      }
                      onClick={() => setSelectedId(p.id)}
                    >
                      <span className="proj-title">{p.title}</span>
                      <span className="proj-meta">
                        {Math.ceil(p.duration_sec / 60)} min ·{" "}
                        {stageLabel(p.stage || p.status)}
                        {p.stage && p.stage !== "ready" && p.progress != null
                          ? ` · ${Math.round(p.progress * 100)}%`
                          : ""}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="dash-card">
            {selectedId && !project ? (
              <p className="dash-sub">Loading project…</p>
            ) : !project ? (
              <p className="dash-sub">
                Select a project to review its ranked moments.
              </p>
            ) : (
              <>
                <h2>{project.title}</h2>
                <p className="dash-sub">
                  {project.source_type} · {fmtTime(project.duration_sec)} ·{" "}
                  {stageLabel(project.job?.stage || project.status)}
                  {jobRunning && project.job
                    ? ` · ${Math.round(project.job.progress * 100)}%`
                    : ""}
                </p>
                {project.job?.error && (
                  <p className="dash-alert" role="alert">
                    {project.job.error}
                  </p>
                )}
                {jobRunning && (
                  <div className="progress">
                    <div
                      className="progress-bar"
                      style={{
                        width: `${Math.round(
                          (project.job?.progress || 0) * 100
                        )}%`,
                      }}
                    />
                  </div>
                )}
                {project.status === "ready" && moments.length === 0 && (
                  <p className="dash-sub">
                    No strong moments found in this VOD — try a livelier
                    stream with chat or loud reactions.
                  </p>
                )}
                {moments.length > 0 && (
                  <>
                    <p className="dash-note">
                      Scores rank clips; they do not guarantee views.
                    </p>
                    <ol className="moment-list">
                      {moments.map((m, idx) => {
                        const cs =
                          clipState[m.id] ||
                          (m.clips[0]
                            ? {
                                clipId: m.clips[0].id,
                                status: m.clips[0].status,
                                stage: m.clips[0].status,
                              }
                            : null);
                        return (
                          <li key={m.id} className="moment">
                            <div className="moment-head">
                              <span className="score">{m.score}</span>
                              <div>
                                <strong>
                                  #{idx + 1} · {fmtTime(m.start_sec)} –{" "}
                                  {fmtTime(m.end_sec)}
                                </strong>
                                <p className="moment-reason">
                                  {m.score_reason}
                                  {m.signals?.audio_spike
                                    ? ` · audio spike ×${m.signals.audio_spike}`
                                    : ""}
                                  {m.signals?.chat_spike
                                    ? ` · chat spike ×${m.signals.chat_spike}`
                                    : ""}
                                </p>
                              </div>
                            </div>
                            <div className="hooks">
                              {m.hooks.map((h, hi) => (
                                <label key={hi} className="hook-opt">
                                  <input
                                    type="radio"
                                    name={`hook-${m.id}`}
                                    checked={(hookChoice[m.id] ?? 0) === hi}
                                    onChange={() => {
                                      setHookChoice((s) => ({
                                        ...s,
                                        [m.id]: hi,
                                      }));
                                      setCustomHook((s) => ({
                                        ...s,
                                        [m.id]: "",
                                      }));
                                    }}
                                  />
                                  <span>{h.text}</span>
                                </label>
                              ))}
                              <input
                                type="text"
                                placeholder="Or write your own hook…"
                                value={customHook[m.id] || ""}
                                onChange={(e) =>
                                  setCustomHook((s) => ({
                                    ...s,
                                    [m.id]: e.target.value,
                                  }))
                                }
                                className="hook-custom"
                              />
                            </div>
                            <div className="moment-actions">
                              {!cs ? (
                                <button
                                  className="btn btn-sm"
                                  onClick={() => makeClip(m)}
                                >
                                  Create clip
                                </button>
                              ) : cs.status === "exported" ? (
                                <a
                                  className="btn btn-sm btn-accent"
                                  href={`${API_URL}/api/clips/${cs.clipId}/download`}
                                >
                                  Download MP4
                                </a>
                              ) : cs.status === "failed" ? (
                                <button
                                  className="btn btn-sm"
                                  onClick={() => makeClip(m)}
                                >
                                  Retry export
                                </button>
                              ) : (
                                <span className="dash-note">
                                  {stageLabel(cs.stage)}…
                                </span>
                              )}
                              <span className="dash-note">
                                9:16 · captions on ·{" "}
                                {credits?.plan === "free"
                                  ? "watermarked"
                                  : "clean"}
                              </span>
                            </div>
                          </li>
                        );
                      })}
                    </ol>
                  </>
                )}
              </>
            )}
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="wrap">
          <span>© 2026 Hookclip.</span>
          <span>
            Hookclip is not affiliated with Rockstar Games or Take-Two
            Interactive.
          </span>
        </div>
      </footer>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="wrap dash-main"><h1>Dashboard</h1><p>Loading…</p></div>}>
      <DashboardInner />
    </Suspense>
  );
}
