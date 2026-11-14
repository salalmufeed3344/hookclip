# Hookclip — AI clipper for GTA VI streams

**Status:** P0 built + verified end-to-end locally (Nov 14, 2026) · **Target:**
landing + waitlist live Nov 14–15, 2026; full P0 live Nov 18, 2026
(GTA VI launches Nov 19). Not deployed yet — deploy needs the owner's
accounts (steps below).

## What it is
Paste a Twitch/YouTube VOD → ranked moments (0–99) with hooks, animated
captions, 9:16 facecam-split reframe → export a clean MP4. Free 60 min/mo;
Starter $9/mo 150 min; Pro $19/mo 400 min. See `../files/pricing.md`.

## Layout
```
hookclip/
  frontend/    Next.js landing page + dashboard (static export → Cloudflare Pages)
  worker/      FastAPI worker: waitlist API + video pipeline (→ DeployXA)
  supabase/    Postgres migrations (the §6 data model)
```

## Local dev
```bash
# Worker (API on :8000, SQLite in worker/data/)
cd worker
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill WAITLIST_ADMIN_TOKEN at minimum
.venv/bin/uvicorn app.main:app --port 8000 --reload

# Frontend (static site on :3000)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
python3 -m http.server 3000 -d out
```

## Waitlist (Milestone 0 — live first)
- Signups land in the worker's SQLite DB (`worker/data/hookclip.db`,
  table `waitlist`). No Supabase needed; nothing is lost if the frontend
  is redeployed.
- Count: `GET /api/waitlist/count`
- Export CSV (owner only):
  `GET /api/waitlist/export?token=<WAITLIST_ADMIN_TOKEN>`

## Dashboard + review UI (F-09, F-12)
- `/dashboard` — credits balance, paste-a-VOD form, project list, live job
  status (polls every 3s), ranked moments with score + plain-words reason,
  3 hook options per moment (or write your own), create clip → export →
  download MP4. Static export: the route is `dashboard.html`, which
  Cloudflare Pages serves at `/dashboard`.
- Local test: `NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build`,
  then serve `out/` — the dashboard talks to the worker on :8000.

## Verified end-to-end (Nov 14, 2026, local sandbox, no keys set)
- Test VOD: YouTube "GTA 5 – The Ballad of Rocco Mission Walkthrough"
  (`SH9jVCyxPk0`, 458 s, 8 credits). Project queued → ready in ~95 s:
  18 transcript segments, 234 words, 0 chat msgs, 52 audio spikes,
  2 moments (scores 42 "loud moment", 32 "loud moment + little dialogue").
  Honest note: a no-commentary walkthrough scores low — that is the
  system working, not failing.
- Clip 1 (moment 181–241 s, 60 s): exported 1080x1920 H.264 + AAC,
  27.6 MB, ~3 min render on 1.5 shared CPUs; free-tier "Hookclip"
  watermark bottom-right; center-crop (no webcam in source — facecam
  split correctly fell back). **Bug found in this clip:** the hook text
  overflowed both edges (single line at 76pt). Fixed in
  `worker/app/render.py` — hook is now pre-wrapped to ≤2 lines with
  `\N`, shrinking to 64pt if needed.
- Clip 2 (same moment, trimmed 153–183 s, 30 s): exported 10.1 MB;
  frames verified visually — hook wraps cleanly to 2 lines, karaoke
  captions render (current word highlighted yellow), watermark present.
- Download endpoint `GET /api/clips/{id}/download` returns the exact
  exported bytes (200, byte-identical).
- Chat-spike logic verified on a synthetic fixture (ratio 4.25 triggers,
  spammer capped at 3/window, Nightbot filtered). Twitch VOD download
  via yt-dlp is UNTESTED from the sandbox (Twitch GraphQL times out
  through the egress proxy) — verify with a real Twitch VOD after
  deploy. YouTube needs `--extractor-args
  "youtube:player_client=tv_embedded"` (default client is bot-gated).
- Waitlist: signup → position, count, CSV export (401 without token)
  all verified; test rows deleted, count back to 0.
- CORS is env-driven (`CORS_ORIGINS`, default localhost:3000/8000) —
  set it to the real frontend origin at deploy or the dashboard's
  browser calls will be blocked (preflight from hookclip.app = 400
  until then).

## Deploy (owner — needs his accounts; nothing here deploys itself)
1. **GitHub repo** (owner creates it; the builder cannot): push this folder.
2. **Domain:** buy `hookclip.app` at a registrar (verify it's still free
   first). Point it at Cloudflare.
3. **Frontend → Cloudflare Pages:** connect the repo, build command
   `npm run build`, output directory `frontend/out`, root `frontend/`.
   Env var: `NEXT_PUBLIC_API_URL` = the worker URL (step 4).
4. **Worker → DeployXA:** connect the repo, root `worker/`, it builds the
   `Dockerfile` (Python 3.12 + ffmpeg). Env vars from `worker/.env.example`:
   `WAITLIST_ADMIN_TOKEN` (generate one), `GROQ_API_KEY`, `GEMINI_API_KEY`,
   `TWITCH_CLIENT_ID`/`TWITCH_CLIENT_SECRET`, and `CORS_ORIGINS` =
   `https://hookclip.app,https://www.hookclip.app` (without this the
   dashboard's browser calls are blocked). Persistent volume mounted at
   `/data` with `DATA_DIR=/data`.
5. **Supabase (free tier):** create a project, run
   `supabase/migrations/001_init.sql`, set `SUPABASE_URL` +
   `SUPABASE_SERVICE_ROLE_KEY` on the worker. Until then the worker uses
   local SQLite — the schema is identical.
6. **R2 (free tier):** create a bucket `hookclip`, set the `R2_*` env vars.
   Until then clips are served from the worker's local disk.
7. **Paddle (STUBBED):** Paddle onboarding needs the owner's ID/business
   verification. When ready, set the `PADDLE_*` vars and the price IDs;
   the credits ledger + plan gating are already built, checkout is the
   only stubbed part.

## API keys (never hardcoded)
All keys come from env vars. Missing keys degrade cleanly: no Groq key →
local faster-whisper; no Gemini key → heuristic scorer; no Twitch keys →
chat/viewer-clip signals skipped; no Paddle keys → checkout stubbed.
`GET /health` reports which integrations are live.
