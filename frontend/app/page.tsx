import WaitlistForm from "../components/WaitlistForm";

export default function Home() {
  return (
    <>
      <header className="site-header">
        <div className="wrap">
          <a className="logo" href="/">
            <span className="logo-mark">▶</span> Hookclip
          </a>
          <nav className="nav">
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="/dashboard">Dashboard</a>
          </nav>
          <a className="btn btn-sm" href="/dashboard">
            Start clipping
          </a>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="wrap">
            <span className="eyebrow">
              <b>GTA VI launches Nov 19, 2026</b> — Hookclip is live now
            </span>
            <h1>
              GTA VI launches Nov 19.{" "}
              <span className="accent">Clippers get paid.</span>
            </h1>
            <p className="lede">
              Brands pay clippers per 1,000 views — a median of about $1 per
              1k, up to ~$200 per viral clip. Hookclip is the $9-a-month tool
              that finds the moments worth clipping: ranked, hooked,
              captioned, and ready to post.
            </p>
            <div className="hero-cta">
              <a className="btn btn-accent btn-lg" href="/dashboard">
                Start clipping free
              </a>
              <a className="hero-alt" href="#updates">
                Get GTA VI clipping tips by email ↓
              </a>
            </div>
            <p className="waitlist-note">
              Free 60 minutes a month. No card required. Live now — paste a
              VOD and get ranked clips in minutes.
            </p>
            <div className="earn-strip">
              <div className="earn-stat">
                <strong>~$1</strong>
                <span>per 1,000 views, median brand rate</span>
              </div>
              <div className="earn-stat">
                <strong>~$200</strong>
                <span>up to, per viral clip</span>
              </div>
              <div className="earn-stat">
                <strong>$9/mo</strong>
                <span>150 minutes of clipping</span>
              </div>
            </div>
            <p className="earn-fine">
              Rates vary by campaign and platform. Earnings are never
              guaranteed — but the upside is real, and the tool costs less
              than one takeaway.
            </p>
          </div>
        </section>

        <section className="section" id="how">
          <div className="wrap">
            <h2>From a 10-hour VOD to post-ready clips</h2>
            <p className="sub">
              No scrubbing, no timeline editing, no guessing what went viral.
              Three steps.
            </p>
            <div className="steps">
              <div className="step">
                <div className="step-num">Step 01</div>
                <h3>Paste a VOD link</h3>
                <p>
                  Drop in a Twitch or YouTube VOD. Hookclip pulls the video
                  and the chat replay — nothing to download or upload.
                </p>
              </div>
              <div className="step">
                <div className="step-num">Step 02</div>
                <h3>Get the ranked moments</h3>
                <p>
                  Chat spikes, loud moments, and the transcript are scored
                  0–99. The best clips come first, each with a plain-words
                  reason and three hook options.
                </p>
              </div>
              <div className="step">
                <div className="step-num">Step 03</div>
                <h3>Export and post</h3>
                <p>
                  9:16 vertical, facecam and gameplay both in frame, captions
                  burned in. Download the MP4 and post it anywhere.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="features">
          <div className="wrap">
            <h2>Everything a clipper needs, nothing they don&rsquo;t</h2>
            <p className="sub">
              Built for the launch wave: speed matters more than a timeline.
            </p>
            <div className="features">
              <div className="feature">
                <span className="tag">Ranked 0–99</span>
                <h3>Best moments first</h3>
                <p>
                  Every candidate moment is scored on hook strength, emotional
                  flow, value, and trend — so you cut the top 10, not the
                  first 10. The score ranks clips; it never promises views.
                </p>
              </div>
              <div className="feature">
                <span className="tag">3 hooks per moment</span>
                <h3>Hooks that hold the first 3 seconds</h3>
                <p>
                  Three opening lines per clip, ranked by predicted hold.
                  Pick one or write your own — it&rsquo;s burned into the
                  first 3 seconds of the export.
                </p>
              </div>
              <div className="feature">
                <span className="tag">Word-by-word</span>
                <h3>Animated captions, done for you</h3>
                <p>
                  TikTok-style captions from the transcript, timed to the
                  word. Fix a wrong word before you export — no retyping.
                </p>
              </div>
              <div className="feature">
                <span className="tag">9:16, facecam split</span>
                <h3>Facecam and gameplay, both visible</h3>
                <p>
                  A plain center-crop cuts the webcam out. Hookclip puts the
                  facecam on top and the gameplay below — or tracks the
                  action when there&rsquo;s no webcam.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="pricing">
          <div className="wrap">
            <h2>Invest $9. Clip all month.</h2>
            <p className="sub">
              One credit is one minute of source video. One viral clip can
              pay for the year — the tool costs less than a single takeaway.
            </p>
            <div className="plans">
              <div className="plan">
                <h3>Free</h3>
                <div className="price">
                  $0<span> / month</span>
                </div>
                <ul>
                  <li>60 source minutes / month</li>
                  <li>Watermarked exports, 720p</li>
                  <li>Ranked moments + hooks + captions</li>
                </ul>
                <a className="btn plan-btn" href="/dashboard">
                  Start free
                </a>
              </div>
              <div className="plan hot">
                <span className="flag">Most popular</span>
                <h3>Starter</h3>
                <div className="price">
                  $9<span> / month</span>
                </div>
                <ul>
                  <li>150 source minutes / month</li>
                  <li>Clean exports, 1080p, no watermark</li>
                  <li>Priority queue</li>
                </ul>
                <a className="btn btn-accent plan-btn" href="/dashboard">
                  Start with Starter
                </a>
              </div>
              <div className="plan">
                <h3>Pro</h3>
                <div className="price">
                  $19<span> / month</span>
                </div>
                <ul>
                  <li>400 source minutes / month</li>
                  <li>Everything in Starter</li>
                  <li>For clip teams and heavy days</li>
                </ul>
                <a className="btn plan-btn" href="/dashboard">
                  Start with Pro
                </a>
              </div>
            </div>
          </div>
        </section>

        <section className="section cta" id="updates">
          <div className="wrap">
            <h2>Get GTA VI clipping tips</h2>
            <p>
              One short email a week until launch — what&rsquo;s working for
              clippers, and what&rsquo;s new in Hookclip. No spam.
            </p>
            <WaitlistForm compact />
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="wrap">
          <span>© 2026 Hookclip. Built for the GTA VI launch wave.</span>
          <span>
            Hookclip is not affiliated with Rockstar Games or Take-Two
            Interactive.
          </span>
        </div>
      </footer>
    </>
  );
}
