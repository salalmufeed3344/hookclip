"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

type PlanId = "starter" | "pro" | "pack" | "free";

const PLANS: Record<
  PlanId,
  {
    name: string;
    price: string;
    priceNote: string;
    minutes: string;
    billing: string;
    total: string;
    features: string[];
    renews: string;
  }
> = {
  starter: {
    name: "Starter",
    price: "$9",
    priceNote: "/ month",
    minutes: "150 source minutes / month",
    billing: "Monthly subscription",
    total: "$9.00",
    features: [
      "150 source minutes / month",
      "Clean exports, 1080p, no watermark",
      "Ranked moments + hooks + captions",
      "Priority queue",
    ],
    renews: "Renews monthly. Cancel anytime — you keep your minutes until the end of the paid month.",
  },
  pro: {
    name: "Pro",
    price: "$19",
    priceNote: "/ month",
    minutes: "400 source minutes / month",
    billing: "Monthly subscription",
    total: "$19.00",
    features: [
      "400 source minutes / month",
      "Everything in Starter",
      "Clean exports, 1080p, no watermark",
      "For clip teams and heavy launch days",
    ],
    renews: "Renews monthly. Cancel anytime — you keep your minutes until the end of the paid month.",
  },
  pack: {
    name: "Credit pack",
    price: "$5",
    priceNote: "one-off",
    minutes: "100 source minutes",
    billing: "One-off purchase",
    total: "$5.00",
    features: [
      "100 source minutes",
      "Clean exports, 1080p, no watermark",
      "No subscription — buy again when you need more",
      "Ranked moments + hooks + captions",
    ],
    renews: "One-off purchase. No subscription, no renewal.",
  },
  free: {
    name: "Free",
    price: "$0",
    priceNote: "/ month",
    minutes: "60 source minutes / month",
    billing: "Free forever",
    total: "$0.00",
    features: [
      "60 source minutes / month",
      "Watermarked exports, 720p",
      "Ranked moments + hooks + captions",
    ],
    renews: "Free — no card, no checkout.",
  },
};

const PLAN_ORDER: PlanId[] = ["starter", "pro", "pack"];

function validPlan(p: string | null): PlanId {
  if (p === "starter" || p === "pro" || p === "pack" || p === "free") return p;
  return "starter";
}

function CheckoutInner() {
  const search = useSearchParams();
  const router = useRouter();
  const [plan, setPlan] = useState<PlanId>(() => validPlan(search.get("plan")));
  const current = PLANS[plan];

  function switchPlan(next: PlanId) {
    setPlan(next);
    router.replace(`/checkout?plan=${next}`, { scroll: false });
  }

  return (
    <div className="dash">
      <header className="site-header">
        <div className="wrap">
          <a className="logo" href="/">
            <span className="logo-mark">▶</span> Hookclip
          </a>
          <nav className="nav">
            <a href="/">Home</a>
            <a href="/#pricing">Pricing</a>
            <a href="/dashboard">Dashboard</a>
          </nav>
          <a className="btn btn-sm" href="/dashboard">
            Dashboard
          </a>
        </div>
      </header>

      <main className="wrap dash-main">
        <h1>Checkout</h1>
        <p className="dash-sub">
          One credit is one minute of source video. Pick a plan — the minutes
          land on your account as soon as payment is connected.
        </p>

        <div className="checkout-layout">
          <div className="dash-card">
            <h2>Choose your plan</h2>
            <div className="plan-switch" role="group" aria-label="Choose a plan">
              {PLAN_ORDER.map((id) => (
                <button
                  key={id}
                  type="button"
                  className={"plan-switch-btn" + (plan === id ? " active" : "")}
                  onClick={() => switchPlan(id)}
                  aria-pressed={plan === id}
                >
                  <strong>{PLANS[id].name}</strong>
                  <span>
                    {PLANS[id].price} {PLANS[id].priceNote}
                  </span>
                </button>
              ))}
            </div>

            <h3 className="checkout-plan-name">
              {current.name} · {current.price}
              <span>{current.priceNote}</span>
            </h3>
            <ul className="checkout-features">
              {current.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <p className="dash-note">{current.renews}</p>
            {plan === "free" && (
              <a className="btn btn-accent" href="/dashboard">
                Start free — no checkout needed
              </a>
            )}
          </div>

          <div className="dash-card">
            <h2>Order summary</h2>
            <dl className="summary">
              <div>
                <dt>Plan</dt>
                <dd>{current.name}</dd>
              </div>
              <div>
                <dt>Minutes</dt>
                <dd>{current.minutes}</dd>
              </div>
              <div>
                <dt>Billing</dt>
                <dd>{current.billing}</dd>
              </div>
              <div className="summary-total">
                <dt>Total due today</dt>
                <dd>{current.total}</dd>
              </div>
            </dl>

            {plan === "free" ? (
              <p className="dash-note">
                The free plan costs nothing — head to the dashboard and paste
                a VOD.
              </p>
            ) : (
              <>
                <button type="button" className="btn btn-accent btn-lg pay-btn" disabled>
                  Continue to secure checkout
                </button>
                <p className="pay-note">
                  Payments run through Paddle and aren&rsquo;t connected yet —
                  this button turns on at launch. You won&rsquo;t be charged
                  anything here.
                </p>
              </>
            )}

            <p className="dash-note">
              Prices in USD. Minutes don&rsquo;t roll over month to month.
              <br />
              <a href="/#pricing">Back to pricing</a>
              {" · "}
              <a href="/dashboard">Back to dashboard</a>
            </p>
          </div>
        </div>
      </main>

      <footer className="site-footer">
        <div className="wrap">
          <span>© 2026 Hookclip.</span>
          <span>
            <a href="/#pricing">Pricing</a>
            {" · "}
            <a href="/dashboard">Dashboard</a>
            {" · "}
            <a href="/checkout?plan=starter">Upgrade</a>
          </span>
          <span>
            Hookclip is not affiliated with Rockstar Games or Take-Two
            Interactive.
          </span>
        </div>
      </footer>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense
      fallback={
        <div className="wrap dash-main">
          <h1>Checkout</h1>
          <p>Loading…</p>
        </div>
      }
    >
      <CheckoutInner />
    </Suspense>
  );
}
