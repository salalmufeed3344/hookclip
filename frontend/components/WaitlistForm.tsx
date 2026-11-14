"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type State =
  | { kind: "idle" }
  | { kind: "busy" }
  | { kind: "done"; position: number }
  | { kind: "error"; message: string };

export default function WaitlistForm({ compact = false }: { compact?: boolean }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("clipper");
  const [state, setState] = useState<State>({ kind: "idle" });
  const [count, setCount] = useState<number | null>(null);

  // Live waitlist count for social proof; silently hidden if the API is down.
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/waitlist/count`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d && typeof d.count === "number") setCount(d.count);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (state.kind === "busy") return;
    setState({ kind: "busy" });
    try {
      const res = await fetch(`${API_URL}/api/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, role }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const msg =
          data?.detail?.[0]?.msg ||
          (typeof data?.detail === "string" ? data.detail : null) ||
          "Something went wrong. Please try again.";
        setState({ kind: "error", message: msg });
        return;
      }
      setState({ kind: "done", position: data?.position ?? 0 });
    } catch {
      setState({
        kind: "error",
        message:
          "Could not reach the signup service. Check your connection and try again — your email was not saved yet.",
      });
    }
  }

  if (state.kind === "done") {
    return (
      <div className="waitlist">
        <div className="waitlist-ok" role="status">
          <strong>You&rsquo;re on the list.</strong>
          <p>
            {state.position > 0
              ? `You are #${state.position} in line. `
              : ""}
            We&rsquo;ll email you first access when Hookclip opens on Nov 18 —
            one day before GTA VI launches.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="waitlist">
      <form onSubmit={submit}>
        <div className="waitlist-row">
          <input
            type="email"
            required
            placeholder="you@example.com"
            aria-label="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={state.kind === "busy"}
          />
          <select
            aria-label="I am a"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            disabled={state.kind === "busy"}
          >
            <option value="clipper">Clipper</option>
            <option value="streamer">Streamer</option>
            <option value="both">Both</option>
            <option value="other">Other</option>
          </select>
          <button
            type="submit"
            className="btn btn-accent"
            disabled={state.kind === "busy"}
          >
            {state.kind === "busy" ? "Joining…" : "Join the waitlist"}
          </button>
        </div>
        {state.kind === "error" && (
          <p className="waitlist-err" role="alert">
            {state.message}
          </p>
        )}
      </form>
      {!compact && (
        <p className="waitlist-note">
          Free 60 minutes a month. No card required.
          {count !== null && count > 0
            ? ` ${count} ${count === 1 ? "person" : "people"} already waiting.`
            : ""}
        </p>
      )}
    </div>
  );
}
