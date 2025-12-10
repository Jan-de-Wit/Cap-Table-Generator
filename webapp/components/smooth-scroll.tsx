"use client";

import { useEffect } from "react";
import Lenis from "lenis";

// Store global Lenis instance so other components can pause/resume it
let globalLenisInstance: Lenis | null = null;

export function getGlobalLenis(): Lenis | null {
  return globalLenisInstance;
}

export function SmoothScroll() {
  useEffect(() => {
    const lenis = new Lenis({
      lerp: 0.05,
      duration: 1.2,
      smoothWheel: true,
      syncTouch: false,
      touchMultiplier: 2,
      wheelMultiplier: 1,
      infinite: false,
      autoResize: true,
      orientation: "vertical",
      gestureOrientation: "vertical",
      anchors: true,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });

    globalLenisInstance = lenis;

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
      globalLenisInstance = null;
    };
  }, []);

  return null;
}

