"use client";

import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

/**
 * All scroll storytelling for the landing page, in one place.
 * GSAP ScrollTrigger, scrub: 1 everywhere, transform + opacity only.
 * Reduced motion: no setup at all — every scene renders in its final state.
 *
 * Branches (mutually exclusive, cover every viewport):
 * - shared: hero load entrance + solution beat reveals.
 * - tall desktop (>=761px wide AND >=800px tall): pinned scenes — hero
 *   two-beat swap, problem VOD scrub, proof row steps, sideways how.
 * - mobile or short desktop: the same moments play once on enter instead
 *   of being pinned/scrubbed (pinned scenes would cut content that is
 *   taller than the viewport).
 */
export default function StoryAnimations() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    gsap.registerPlugin(ScrollTrigger);
    const mm = gsap.matchMedia();

    // Shared on every viewport.
    mm.add("(min-width: 0px)", () => {
      // Hero load entrance: frame settles, copy rises (title first).
      gsap.from(".hero-beat-1 .hero-copy > *", {
        opacity: 0,
        y: 20,
        duration: 0.7,
        ease: "power3.out",
        stagger: 0.09,
      });
      gsap.from(".hero-frame", {
        opacity: 0,
        scale: 1.05,
        duration: 1,
        ease: "power3.out",
      });

      // Solution beats: one entrance each, once, on scroll-in.
      gsap.utils.toArray<HTMLElement>(".beat").forEach((beat) => {
        gsap.from(beat, {
          opacity: 0,
          y: 24,
          duration: 0.6,
          ease: "power3.out",
          scrollTrigger: {
            trigger: beat,
            start: "top 85%",
            toggleActions: "play none none none",
          },
        });
      });
    });

    // Tall desktop: pinned, scrubbed scenes.
    mm.add("(min-width: 761px) and (min-height: 800px)", () => {
      // Hero pin: scroll swaps beat 1 (result) for beat 2 (fear).
      gsap.to(".hero-track", {
        yPercent: -50,
        ease: "none",
        scrollTrigger: {
          trigger: ".story-hero",
          start: "top top",
          end: "+=70%",
          scrub: 1,
          pin: true,
          anticipatePin: 1,
        },
      });

      // Hero frame parallax: the frame drifts up as the hero leaves.
      gsap.to(".hero-frame", {
        yPercent: -8,
        ease: "none",
        scrollTrigger: {
          trigger: ".story-hero",
          start: "top top",
          end: "bottom top",
          scrub: 1,
        },
      });

      // Problem scrub: the playhead crosses a 10-hour VOD.
      const problemTl = gsap.timeline({
        scrollTrigger: {
          trigger: ".problem-stage",
          start: "top top",
          end: "+=140%",
          scrub: 1,
          pin: true,
          anticipatePin: 1,
          onUpdate: (self) => {
            const el = document.querySelector(".vod-time");
            if (!el) return;
            const total = Math.round(self.progress * 600);
            const h = Math.floor(total / 60);
            const m = String(total % 60).padStart(2, "0");
            el.textContent = `${h}:${m} / 10:00`;
          },
        },
      });
      problemTl
        .from(".vod-fill", { scaleX: 0, transformOrigin: "left center", ease: "none", duration: 3.4 }, 0)
        .from(".vod-bar", { scaleY: 0, transformOrigin: "bottom", ease: "none", stagger: 0.08, duration: 3.4 }, 0)
        .from(".vod-found", { opacity: 0, y: 12, ease: "none", duration: 0.4 }, 2.75)
        .from(".problem-close", { opacity: 0, y: 12, ease: "none", duration: 0.4 }, 3.0);

      // Proof rows reveal one per scroll step, panel pinned.
      const proofTl = gsap.timeline({
        scrollTrigger: {
          trigger: ".story-proof",
          start: "top top",
          end: "+=150%",
          scrub: 1,
          pin: true,
          anticipatePin: 1,
        },
      });
      proofTl
        .from(".proof-row", { opacity: 0, y: 14, ease: "none", stagger: 0.4 }, 0)
        .from(".proof-earn", { opacity: 0, y: 10, ease: "none", duration: 0.3 }, 1.2);

      // How-it-works scrolls sideways, pinned.
      gsap.to(".how-track", {
        x: "-200vw",
        ease: "none",
        scrollTrigger: {
          trigger: ".story-how",
          start: "top top",
          end: "+=170%",
          scrub: 1,
          pin: true,
          anticipatePin: 1,
          invalidateOnRefresh: true,
        },
      });
    });

    // Mobile or short desktop: the same moments play once on enter.
    mm.add(
      "(max-width: 760px), (min-width: 761px) and (max-height: 799px)",
      () => {
        // Problem: the scrub plays once when it scrolls in; the readout
        // lands on the spike time (bar 19 of 24 ≈ 8:07 into the VOD).
        gsap.from(".vod-fill", {
          scaleX: 0,
          transformOrigin: "left center",
          duration: 1.2,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".vod-scrub",
            start: "top 75%",
            toggleActions: "play none none none",
          },
        });
        gsap.from(".vod-bar", {
          scaleY: 0,
          transformOrigin: "bottom",
          duration: 0.6,
          ease: "power2.out",
          stagger: 0.03,
          scrollTrigger: {
            trigger: ".vod-scrub",
            start: "top 75%",
            toggleActions: "play none none none",
          },
        });
        gsap.from(".vod-found, .problem-close", {
          opacity: 0,
          y: 12,
          duration: 0.5,
          ease: "power3.out",
          stagger: 0.15,
          onStart: () => {
            const el = document.querySelector(".vod-time");
            if (el) el.textContent = "8:07 / 10:00";
          },
          scrollTrigger: {
            trigger: ".vod-found",
            start: "top 85%",
            toggleActions: "play none none none",
          },
        });

        gsap.from(".proof-row", {
          opacity: 0,
          y: 14,
          duration: 0.5,
          ease: "power3.out",
          stagger: 0.12,
          scrollTrigger: {
            trigger: ".product-panel",
            start: "top 80%",
            toggleActions: "play none none none",
          },
        });
        gsap.from(".proof-earn", {
          opacity: 0,
          y: 10,
          duration: 0.5,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".proof-earn",
            start: "top 90%",
            toggleActions: "play none none none",
          },
        });
        gsap.utils.toArray<HTMLElement>(".how-panel").forEach((panel) => {
          gsap.from(panel, {
            opacity: 0,
            y: 24,
            duration: 0.6,
            ease: "power3.out",
            scrollTrigger: {
              trigger: panel,
              start: "top 85%",
              toggleActions: "play none none none",
            },
          });
        });
      }
    );

    return () => mm.revert();
  }, []);

  return null;
}
