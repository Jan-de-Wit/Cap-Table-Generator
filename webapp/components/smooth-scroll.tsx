"use client";

import { useEffect } from "react";
import Lenis from "lenis";

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
      touchInertiaMultiplier: 35,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  return null;
}

