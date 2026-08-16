'use client';

import { useEffect } from 'react';

// In an installed (standalone) PWA — especially on iOS — the CSS layout
// viewport (what 100vh / 100dvh / -webkit-fill-available resolve to) is
// shorter than the actual screen: the former browser toolbar strip is still
// reserved, leaving a blank gap below the app. The VisualViewport API always
// reports the true visible height, so we mirror it into a CSS variable that
// sizes the app shell (see globals.css).
export function ViewportHeight() {
  useEffect(() => {
    const root = document.documentElement;

    const sync = () => {
      const height = window.visualViewport?.height ?? window.innerHeight;
      root.style.setProperty('--app-viewport-height', `${Math.round(height)}px`);
    };

    sync();
    window.visualViewport?.addEventListener('resize', sync);
    window.addEventListener('resize', sync);
    window.addEventListener('orientationchange', sync);

    return () => {
      window.visualViewport?.removeEventListener('resize', sync);
      window.removeEventListener('resize', sync);
      window.removeEventListener('orientationchange', sync);
    };
  }, []);

  return null;
}
