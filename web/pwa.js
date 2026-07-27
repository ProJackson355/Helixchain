/* PWA install + service-worker registration.
 *
 * Kept in an external same-origin file (not inline) so it complies with the
 * site's Content-Security-Policy (script-src 'self'), which blocks inline
 * scripts. Registers the service worker and offers a cross-platform install
 * affordance: the native prompt on Android/desktop, and Add-to-Home-Screen
 * guidance on iOS (which has no programmatic prompt).
 */
(function () {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' });
        await registration.update();
      } catch (_) {}
    });
  }

  function installButton() {
    let b = document.getElementById('pwa-install');
    if (b) return b;
    b = document.createElement('button');
    b.id = 'pwa-install';
    b.type = 'button';
    b.textContent = 'Install Helix app';
    b.style.cssText = 'position:fixed;left:16px;bottom:16px;z-index:60;display:none;padding:9px 15px;border:none;border-radius:11px;font:600 13px/1 "Segoe UI",system-ui,sans-serif;color:#fff;background:linear-gradient(130deg,#7c5cfc,#5b8af7);box-shadow:0 6px 18px -6px rgba(108,99,255,.67);cursor:pointer';
    document.body.appendChild(b);
    return b;
  }

  const standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;

  let deferredPrompt = null;
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredPrompt = event;
    const b = installButton();
    b.style.display = 'block';
    b.onclick = async () => {
      b.style.display = 'none';
      deferredPrompt.prompt();
      try { await deferredPrompt.userChoice; } catch (_) {}
      deferredPrompt = null;
    };
  });

  window.addEventListener('appinstalled', () => {
    const b = document.getElementById('pwa-install');
    if (b) b.style.display = 'none';
  });

  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (isIOS && !standalone) {
    const b = installButton();
    b.style.display = 'block';
    b.onclick = () => alert('To install Helix: tap the Share button, then choose "Add to Home Screen".');
  }
})();
