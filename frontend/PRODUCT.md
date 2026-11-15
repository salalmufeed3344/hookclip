# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Clippers** (primary): people who clip streamers' GTA VI gameplay and post the clips to TikTok / Reels / Shorts to earn money from brand clip campaigns (Whop Content Rewards). They paste a long VOD link, get ranked moments with hooks and captions, export a 9:16 MP4, and post fast. They work in the launch wave, where speed matters more than timeline editing.
- **Streamers** (secondary): GTA VI streamers who want their best moments clipped, or who run clip contests for their community.
- **Clip teams** (Pro plan): heavy users clipping many hours a day.

## Product Purpose

Hookclip turns long GTA VI streams into ranked, hooked, captioned vertical clips. It finds the best moments (chat spikes, loud moments, transcript), scores them 0–99 with a plain-words reason, writes three hooks per moment, reframes to 9:16 with the facecam visible, burns in animated captions, and exports an MP4 ready to post. Success is a stranger pasting a Twitch VOD link and getting ranked clips with hooks and captions, then exporting a clean 9:16 MP4.

## Positioning

The cheapest clipper built specifically for the GTA VI launch wave. Chat-spike detection with clips starting 20 seconds early (chat reacts after the moment), audio-spike detection, and ranking that never promises views. Undercuts the incumbents: OpusClip Starter $15/mo for 150 min and OpenShorts Cloud $12/mo for 100 min — Hookclip Starter is $9/mo for 150 min. Marketing leads with earning (clippers get paid per 1,000 views), product second.

## Operating Context

- GTA VI launches Thursday Nov 19, 2026, PS5 + Xbox Series X|S only, no PC at launch — all clip supply is console streams.
- Twitch VODs are the launch source. YouTube is bot-blocked from the DeployXA worker's egress IP (yt-dlp 400 cookies/auth) — Twitch-only for launch.
- The worker is a FastAPI app on DeployXA (free tier); the frontend is a Next.js static export on Cloudflare Pages. Redeploys wipe the worker's SQLite state (no persistence yet).
- Pricing: Free 60 min/mo (watermarked 720p); Starter $9/mo 150 min; Pro $19/mo 400 min; $5 one-off 100-min pack. 1 credit = 1 source minute. Paddle is the payment provider (5% + $0.50) but is NOT connected yet — checkout is a placeholder.

## Capabilities and Constraints

- P0 (built and live): VOD import, transcription with word timings, chat-spike + audio-spike detection, ranking 0–99 + reason, 3 hooks/moment, 9:16 facecam-split reframe, animated captions (Remotion for clips ≤30s, ffmpeg+ASS fallback), review UI, MP4 export, dashboard + live job status.
- Clip stack integrated Nov 15, 2026: WhisperX (transcription), PySceneDetect (scene cuts), Auto-Editor (silence trim), Remotion, FFmpeg.
- Auth gap (undecided): every visitor currently shares one dev account — per-visitor anonymous accounts vs proper Supabase sign-in is an open decision.
- Payments gap: Paddle onboarding needs the founder's ID; checkout button is disabled until then.
- No fake social proof may be invented: the waitlist and user counts are real (currently near zero) and must not be fabricated. Earnings claims use verified medians only (~$1 per 1,000 views, ~$200 per-clip cap) and never promise guaranteed income.

## Brand Commitments

- Name: Hookclip. Live at hookclip.pages.dev (frontend) and hookclip.deployxa.online (worker). Repo: github.com/salalmufeed3344/hookclip.
- Look: light, clean, professional. One red accent (#e63b2e). No AI-slop tells: no purple-black palette, no glow orbs, no dot grids, no liquid glass, no rainbow coloring, no bento grids, no terminal windows, no sparkle icons, no emojis in headings, no "it's not X, it's Y" copy.
- Nov 15, 2026: Salal picked **Dark, Linear-style** for Hookclip (over light product-led and loud creator energy) — near-black ground (#0a0a0b), hairlines, one red accent (now #d92d20 for contrast), system font stack, real dashboard UI in the hero. Dark is now the Hookclip world; the light look is superseded. Recorded in frontend/DESIGN.md + PRODUCT.md.
- Voice: direct, earn-first, honest about what scores do (they rank clips; they never promise views).
- Legal: not affiliated with Rockstar Games or Take-Two Interactive (stated in the footer).

## Evidence on Hand

- Live product: https://hookclip.pages.dev, https://hookclip.deployxa.online (health ok).
- Local E2E passed on a GTA V VOD (458s): 2 moments, exported 1080×1920 clips with captions + watermark.
- Clip-stack local E2E Nov 15, 2026: WhisperX 314 words, PySceneDetect 18 cuts, Auto-Editor trimmed 4.3s, Remotion verified on a 20s clip.
- Competitor prices verified: OpusClip, Vizard, ClipBot, Hypecut, OpenShorts Cloud, Spikes Studio.

## Product Principles

1. Earn first, product second — the visitor's money is the story, the tool is the means.
2. Speed over editing — the clipper's job is picking the top moments, not scrubbing timelines.
3. Honest scores — ranking is a guide, never a promise of views or income.
4. Cheapest in the category — undercut incumbents on price per minute, always.
5. Degrade gracefully — every enhancement (WhisperX, Remotion, scene detection) falls back to a working path; a clip is never lost to a render tool failing.

## Accessibility & Inclusion

No product-specific accessibility requirement has been established. The site must remain readable and usable without JavaScript-dependent content for the landing page's core message (the checkout and dashboard require JavaScript, as they are app screens).
