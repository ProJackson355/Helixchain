/* Helix Wallet service worker.
 *
 * Deliberately NETWORK-FIRST so an updated app.js/index.html always wins when
 * online — this avoids the stale-cache problem a naive cache-first worker would
 * create. The cache is only a fallback for offline use. API traffic and any
 * non-GET request are never touched, so wallet actions always hit the live node.
 */
const CACHE = 'helix-shell-v6';
// Only paths served identically by both a self-hosted node and Cloudflare Pages,
// so addAll never fails. Scripts (app.js, qrcode.js) are cached at runtime.
const SHELL = [
  '/', '/index.html', '/manifest.webmanifest',
  '/app.js?v=20260738', '/pwa.js?v=3', '/qrcode.js?v=1', '/jsqr.js?v=1',
  '/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-512.png',
  '/secp256k1.js?v=2.2.0',
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).catch(() => {}));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;                       // never cache writes
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;            // only same-origin
  if (url.pathname.startsWith('/api/')) return;               // never cache node/API calls

  // Network-first: use the live copy, fall back to cache only when offline.
  event.respondWith((async () => {
    try {
      const response = await fetch(request);
      if (response && response.ok) {
        const copy = response.clone();
        caches.open(CACHE).then(c => c.put(request, copy)).catch(() => {});
      }
      return response;
    } catch (_) {
      const cached = await caches.match(request);
      return cached || caches.match('/index.html');
    }
  })());
});
