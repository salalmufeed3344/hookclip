import WaitlistForm from "../components/WaitlistForm";
import MotionReveal from "../components/MotionReveal";
import { CLIP_FRAME_SRC } from "./clipFrame";

function PlayMark() {
  return (
    <span className="logo-mark" aria-hidden="true">
      <svg width="12" height="14" viewBox="0 0 12 14" fill="none">
        <path d="M1 1.5v11l10-5.5-10-5.5Z" fill="#0a0a0b" />
      </svg>
    </span>
  );
}

export default function Home() {
  return (
    <>
      <header className="site-header">
        <div className="wrap">
          <a className="logo" href="/">
            <PlayMark /> Hookclip
          </a>
          <nav className="nav">
            <a href="#proof">Proof</a>
            <a href="#problem">Problem</a>
            <a href="#how">How it works</a>
            <a href="#pricing">Pricing</a>
            <a href="#faq">FAQ</a>
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
            <p className="hero-pill anim-pill">
              GTA VI launches Nov 19, 2026 · PS5 + Xbox
            </p>
            <h1 className="anim-title">
              Turn GTA VI streams into clips that pay.
            </h1>
            <p className="lede anim-lede">
              Every stream is hours of footage with seconds worth posting.
              Hookclip finds those seconds, ranks them, and hands you a 9:16
              clip ready to post, while the wave is still moving.
            </p>
            <div className="hero-cta anim-cta">
              <a className="btn btn-accent btn-lg" href="/dashboard">
                Start clipping free
              </a>
              <a className="hero-alt" href="#proof">
                See the proof ↓
              </a>
            </div>
            <p className="hero-fear anim-fear">
              Wait a week and the same clip is worth nothing. The wave does
              not come back.
            </p>
          </div>
        </section>

        <section className="section" id="proof">
          <div className="wrap">
            <h2>Don&rsquo;t take our word for it. Take the VOD.</h2>
            <p className="sub">
              This is what Hookclip returned for one 2-hour Twitch stream.
              Ranked moments, hooks, captions, export.
            </p>
            <MotionReveal className="motion-reveal">
              <div className="product-panel">
                <div className="panel-head">
                  <strong>Ranked moments</strong>
                  <span>Sample VOD · Twitch · 2h 14m</span>
                </div>
                <div className="panel-body">
                  <div className="panel-moments">
                    <div className="moment-row" style={{ "--d": "0ms" } as React.CSSProperties}>
                      <span className="score-chip top">87</span>
                      <div>
                        <strong>#1 · 1:24:10 – 1:25:00</strong>
                        <p>
                          Chat explodes as the heist goes sideways — 4.2× the
                          usual chat rate.
                        </p>
                        <p className="hook">
                          Hook: “The heist went wrong in the best way
                          possible”
                        </p>
                      </div>
                    </div>
                    <div className="moment-row" style={{ "--d": "70ms" } as React.CSSProperties}>
                      <span className="score-chip">76</span>
                      <div>
                        <strong>#2 · 0:42:35 – 0:43:20</strong>
                        <p>
                          Crowd roar and a chat spike when the crew barely
                          escapes.
                        </p>
                        <p className="hook">
                          Hook: “They should NOT have survived that”
                        </p>
                      </div>
                    </div>
                    <div className="moment-row" style={{ "--d": "120ms" } as React.CSSProperties}>
                      <span className="score-chip">68</span>
                      <div>
                        <strong>#3 · 2:03:05 – 2:03:50</strong>
                        <p>
                          A quiet-to-loud flip — the setup pays off in the
                          last five seconds.
                        </p>
                        <p className="hook">
                          Hook: “Wait for the last five seconds”
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="panel-clip">
                    <div className="clip-frame">
                      <img
                        src={CLIP_FRAME_SRC}
                        alt="A vertical clip frame from a night-city scene, with captions"
                      />
                      <div className="clip-caption">
                        HE JUST DID WHAT?!
                        <span>9:16 · captions on</span>
                      </div>
                    </div>
                    <span className="clip-meta">Clip #1 · 50s · clean export</span>
                  </div>
                </div>
              </div>
            </MotionReveal>
            <p className="panel-caption">
              Sample VOD — your ranked moments appear here after you paste
              a link.
            </p>
            <p className="proof-earn">
              Brands pay ~$1 per 1,000 views, up to ~$200 per viral clip
              (verified medians). Earnings are never guaranteed.
            </p>
          </div>
        </section>

        <section className="section" id="problem">
          <div className="wrap">
            <h2>The wave is coming. The footage is already piling up.</h2>
            <p className="sub">
              A long stream runs 8 to 10 hours. The clip that earns is 30 to
              60 seconds. Finding it means watching the whole thing, and by
              the time you find it, someone else has posted it.
            </p>
            <div className="cost-list">
              <div className="cost-row">
                <span className="cost-num">8–10 hours</span>
                <p>
                  A long stream, start to finish. That is the footage you
                  have to get through to find one moment.
                </p>
              </div>
              <div className="cost-row">
                <span className="cost-num">30–60 seconds</span>
                <p>
                  The part worth posting. It hides somewhere in the middle,
                  and the chat only tells you after it happened.
                </p>
              </div>
              <div className="cost-row">
                <span className="cost-num">7 days</span>
                <p>
                  The earning window for a clip. After that the wave moves
                  on, and the same moment is worth nothing.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="solution">
          <div className="wrap">
            <h2>The better way: Hookclip watches, you post.</h2>
            <p className="sub">
              Built for the launch wave: speed matters more than a timeline.
            </p>
            <div className="solution-rows">
              <div className="solution-row">
                <div>
                  <h3>Cut the top 10 moments, not the first 10</h3>
                  <p>
                    Every candidate moment is scored 0–99 on hook strength,
                    emotional flow, value, and trend. The score ranks clips;
                    it never promises views.
                  </p>
                </div>
                <div className="solution-visual">
                  <div className="score-chips">
                    <span className="score-chip top">87</span>
                    <span className="score-chip">76</span>
                    <span className="score-chip">68</span>
                  </div>
                </div>
              </div>
              <div className="solution-row">
                <div>
                  <h3>Start the clip before chat reacts</h3>
                  <p>
                    Chat explodes after the moment happens. Hookclip reads
                    the spike and starts the clip 20 seconds early, so the
                    moment is in the frame, not before it.
                  </p>
                </div>
                <div className="solution-visual">
                  <div className="chat-bars" aria-hidden="true">
                    <i style={{ height: "22%" }} />
                    <i style={{ height: "30%" }} />
                    <i style={{ height: "18%" }} />
                    <i style={{ height: "34%" }} />
                    <i style={{ height: "26%" }} />
                    <i style={{ height: "40%" }} />
                    <i style={{ height: "28%" }} />
                    <i style={{ height: "46%" }} />
                    <i className="spike" style={{ height: "100%" }} />
                    <i style={{ height: "52%" }} />
                    <i style={{ height: "30%" }} />
                    <i style={{ height: "24%" }} />
                  </div>
                  <span className="visual-cap">Chat messages per 10s</span>
                </div>
              </div>
              <div className="solution-row">
                <div>
                  <h3>Hold the first 3 seconds</h3>
                  <p>
                    Three opening lines per clip, ranked by predicted hold.
                    Pick one or write your own. It is burned into the first
                    3 seconds of the export.
                  </p>
                </div>
                <div className="solution-visual">
                  <div className="hook-lines">
                    <span>“The heist went wrong in the best way”</span>
                    <span>“They should NOT have survived that”</span>
                    <span>“Wait for the last five seconds”</span>
                  </div>
                </div>
              </div>
              <div className="solution-row">
                <div>
                  <h3>Watchable with the sound off</h3>
                  <p>
                    TikTok-style captions from the transcript, timed to the
                    word. Fix a wrong word before you export. No retyping.
                  </p>
                </div>
                <div className="solution-visual">
                  <div className="caption-words">
                    HE JUST DID
                    <br />
                    <span>WHAT?!</span>
                  </div>
                </div>
              </div>
              <div className="solution-row">
                <div>
                  <h3>Facecam and gameplay, both visible</h3>
                  <p>
                    A plain center crop cuts the webcam out of a 9:16 clip. Hookclip puts
                    the facecam on top and the gameplay below, or tracks the
                    action when there is no webcam.
                  </p>
                </div>
                <div className="solution-visual">
                  <div className="split-frame" aria-hidden="true">
                    <i className="split-face" />
                    <i className="split-game" />
                  </div>
                  <span className="visual-cap">Facecam on top · gameplay below</span>
                </div>
              </div>
              <div className="solution-row">
                <div>
                  <h3>From VOD to post in minutes</h3>
                  <p>
                    Clean 1080p MP4, captions burned in, no watermark on
                    paid plans. Download it and post it anywhere.
                  </p>
                </div>
                <div className="solution-visual">
                  <div className="export-chip">
                    clip-01.mp4
                    <span>1080×1920 · clean · 50s</span>
                  </div>
                  <div className="export-bar" aria-hidden="true">
                    <i />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="how">
          <div className="wrap">
            <h2>From a 10-hour VOD to post-ready clips</h2>
            <p className="sub">
              No scrubbing, no timeline editing, no guessing what went viral.
              Three steps.
            </p>
            <div className="steps-list">
              <div className="step-row">
                <div className="step-num">1</div>
                <div>
                  <h3>Paste a VOD link</h3>
                  <p>
                    Drop in a Twitch VOD. Hookclip pulls the video and the
                    chat replay — nothing to download or upload.
                  </p>
                </div>
              </div>
              <div className="step-row">
                <div className="step-num">2</div>
                <div>
                  <h3>Get the ranked moments</h3>
                  <p>
                    Chat spikes, loud moments, and the transcript are scored
                    0–99. The best clips come first, each with a plain-words
                    reason and three hook options.
                  </p>
                </div>
              </div>
              <div className="step-row">
                <div className="step-num">3</div>
                <div>
                  <h3>Export and post</h3>
                  <p>
                    9:16 vertical, facecam and gameplay both in frame,
                    captions burned in. Download the MP4 and post it anywhere.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="pricing">
          <div className="wrap">
            <h2>Invest $9. Clip all month.</h2>
            <p className="sub">
              One credit is one minute of source video. One viral clip can
              pay for the year, and the tool costs less than a single
              takeaway.
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
                <a className="btn btn-accent plan-btn" href="/checkout?plan=starter">
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
                <a className="btn plan-btn" href="/checkout?plan=pro">
                  Start with Pro
                </a>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="faq">
          <div className="wrap">
            <h2>Questions, answered</h2>
            <p className="sub">
              The honest version — including the limits.
            </p>
            <div className="faq">
              <div className="faq-row">
                <h3>How do clippers actually get paid?</h3>
                <p>
                  Brands run clip campaigns — for example on Whop — paying
                  per 1,000 views, a median of about $1 per 1k and up to
                  ~$200 per viral clip. Hookclip doesn&rsquo;t pay you; it
                  finds the clips worth posting. Earnings are never
                  guaranteed.
                </p>
              </div>
              <div className="faq-row">
                <h3>Does it work with YouTube?</h3>
                <p>
                  Paste a Twitch VOD today. YouTube is blocked on our servers
                  for now — their bot checks flag our IPs — so Twitch is the
                  launch source.
                </p>
              </div>
              <div className="faq-row">
                <h3>What does the free plan include?</h3>
                <p>
                  60 source minutes a month, watermarked 720p exports, ranked
                  moments with hooks and captions. No card required.
                </p>
              </div>
              <div className="faq-row">
                <h3>Do unused minutes roll over?</h3>
                <p>
                  No. Minutes reset every month. The $5 credit pack is the
                  one-off option if you only need minutes once.
                </p>
              </div>
              <div className="faq-row">
                <h3>Can I cancel anytime?</h3>
                <p>
                  Yes. Monthly plans renew until you cancel, and you keep
                  your minutes until the end of the paid month.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="section cta" id="updates">
          <div className="wrap">
            <h2>GTA VI launches Nov 19. Be ready with clips, not footage.</h2>
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
          <div className="footer-cols">
            <div>
              <a className="logo" href="/">
                <PlayMark /> Hookclip
              </a>
              <p>
                Built for the GTA VI launch wave. Find the moments, post the
                clips, get paid per view.
              </p>
            </div>
            <div>
              <h4>Product</h4>
              <ul>
                <li>
                  <a href="/dashboard">Dashboard</a>
                </li>
                <li>
                  <a href="#pricing">Pricing</a>
                </li>
                <li>
                  <a href="/checkout?plan=starter">Upgrade</a>
                </li>
              </ul>
            </div>
            <div>
              <h4>Learn</h4>
              <ul>
                <li>
                  <a href="#proof">Proof</a>
                </li>
                <li>
                  <a href="#problem">Problem</a>
                </li>
                <li>
                  <a href="#how">How it works</a>
                </li>
                <li>
                  <a href="#faq">FAQ</a>
                </li>
              </ul>
            </div>
          </div>
          <div className="footer-base">
            <span>© 2026 Hookclip.</span>
            <span>
              Hookclip is not affiliated with Rockstar Games or Take-Two
              Interactive.
            </span>
          </div>
        </div>
      </footer>
    </>
  );
}
