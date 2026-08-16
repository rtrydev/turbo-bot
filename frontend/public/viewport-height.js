// Sets --app-viewport-height to the true visible viewport height so the app
// shell (see globals.css) runs edge to edge. In an installed PWA — especially
// on iOS — the CSS layout viewport (100vh / 100dvh) is shorter than the real
// screen, leaving a blank strip below the app; the VisualViewport API always
// reports the true height. Loaded with strategy="beforeInteractive" so the
// value is available before first paint.
(function () {
  'use strict';
  function sync() {
    var height =
      (window.visualViewport && window.visualViewport.height) || window.innerHeight;
    if (height) {
      document.documentElement.style.setProperty(
        '--app-viewport-height',
        Math.round(height) + 'px',
      );
    }
  }
  sync();
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', sync);
  }
  window.addEventListener('resize', sync);
  window.addEventListener('orientationchange', sync);
})();
