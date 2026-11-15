"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Adds `is-visible` to its wrapper the first time it scrolls into view.
 * The CSS only hides content under a `.js` parent class (added here on
 * mount), so with JS off or before hydration the content stays visible.
 * Under prefers-reduced-motion the content shows immediately, with no
 * stagger and no movement.
 */
export default function MotionReveal({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    document.documentElement.classList.add("js");
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setVisible(true);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      },
      { threshold: 0.2 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div ref={ref} className={`${className}${visible ? " is-visible" : ""}`}>
      {children}
    </div>
  );
}
