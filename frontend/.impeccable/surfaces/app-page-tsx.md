---
version: 1
slug: "app-page-tsx"
primary_target: "app/page.tsx"
related_targets: []
---

## Direction contract (v3 — Nov 15, 2026. Salal rejected v2 as "exactly the same it was before": the order changed but the look did not — same dark world, same type, same hairlines, same first viewport. v3 changes the TELLING, not just the order. Salal picked "Storytelling scroll page".)

THESIS: The page is a scroll-driven story in the ayzz order (hero → proof → problem → solution → how → pricing → FAQ → final CTA), told with GSAP ScrollTrigger — the tool @raishancard's saved reel names ("Not just a website, make a full experience for the users. GSAP lets you have that power."). Each beat is a scene, not a section: the hero is a pinned two-beat scene (result, then fear); the problem is a pinned 10-hour VOD timeline the visitor scrubs with their scroll until the 40-second spike erupts; the proof panel's rows reveal one per scroll step; the solution is six full-height chapter beats with big numerals and large visuals; how-it-works is a pinned horizontal scroll. The first viewport is unrecognizable from v1/v2: huge display type (up to 128px) layered over the tall night-city frame, not a centered stack. Pricing, FAQ and final CTA stay as plain decision sections — the story ends, the decision happens.

OWN-WORLD: Same dark tokens (near-black #0a0a0b, hairlines #232326, one red #d92d20, system stack) — the world is the same, the experience is not. What changes is scale, layering and scroll-driven motion. Motion follows Emil Kowalski's rules where they apply (transform + opacity only, strong ease-out, no scale(0)) plus GSAP ScrollTrigger for scrubbed, pinned scenes: scrub: 1 everywhere, one entrance per container, no uniform stagger. Under prefers-reduced-motion ALL ScrollTrigger setup is skipped and every scene renders in its final state (pinned sections become normal flow).

STORY: The visitor is a clipper on GTA VI launch week. Scroll 1: the result (clips that pay) then the fear (the wave does not come back). Scroll 2: they scrub 10 hours of footage with their own scroll and feel the problem before it is explained. Scroll 3: the proof — a real VOD turned into ranked clips, one row per scroll step. Scroll 4: the solution, six chapters, each a benefit with its mechanism shown large. Scroll 5: three steps, sideways. Then the decision: pricing, FAQ, final CTA. Every number is verified and every earning claim carries the never-guaranteed caveat.

FIRST VIEWPORT: Sticky dark header (drawn play-mark logo left, nav: Story / Problem / Proof / How it works / Pricing / FAQ, Start clipping button). Full-viewport hero: the tall night-city frame on the right, headline layered over it on the left at up to 128px ("Turn GTA VI streams into clips that pay."), pill, lede, CTAs. No centered stack, no product panel in the hero.

FORM: Dark, GSAP storytelling scroll page. seed: none (unavailable)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
