// Recall — Memory Dashboard App JS
// This connects to the Anna App Runtime via the SDK injected by the host.
// The SDK is loaded by the host — we just use `window.anna` once it's ready.

(async () => {
  // The host injects the AnnaAppRuntime SDK into the iframe.
  // It's available as window.anna after the iframe loads.
  // We wait for it and then let index.html take over.

  function waitForAnna(maxWait = 10000) {
    return new Promise((resolve, reject) => {
      const start = Date.now();
      function check() {
        if (window.anna && window.anna.tools && window.anna.window) {
          resolve(window.anna);
          return;
        }
        if (Date.now() - start > maxWait) {
          reject(new Error('Anna SDK not available after ' + maxWait + 'ms'));
          return;
        }
        setTimeout(check, 50);
      }
      check();
    });
  }

  try {
    const anna = await waitForAnna();
    console.log('[Recall] Anna SDK ready');

    // Set window title
    if (anna.window && anna.window.setTitle) {
      await anna.window.setTitle('Recall — Memory Dashboard');
    }

    // Signal readiness so the host knows we're loaded
    if (anna.window && anna.window.ready) {
      await anna.window.ready();
    }
  } catch (e) {
    console.error('[Recall] Failed to connect to Anna SDK:', e);
    document.body.innerHTML = '<div style="color:#f85149;text-align:center;padding:48px;">Failed to load Anna SDK. Make sure the app is running in the Anna App Runtime.</div>';
  }
})();
