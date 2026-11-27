/* ================================================================
   Redline service worker — installable PWA + airplane mode.

   Strategy:
   • install  → precache the app shell + the four CDN libraries
     (pdf.js, mammoth, tesseract) so the FIRST offline visit works.
   • fetch    → stale-while-revalidate for CDN hosts (jsdelivr,
     cdnjs, tessdata, gstatic) — after one online OCR pass the
     Tesseract worker/wasm/eng.traineddata are cached too, so OCR
     runs with the radio off.
   • Firebase API calls (firestore/identitytoolkit/aiplatform/
     cloudfunctions) are NEVER cached — network only, and the app
     degrades honestly (on-device pipeline / queued receipts).
   • Bump VERSION to ship an update; old caches are purged on activate.
   ================================================================ */
const VERSION = 'redline-v1.4';
const SHELL   = `${VERSION}-shell`;
const RUNTIME = `${VERSION}-runtime`;

const PRECACHE = [
  './index.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png', './icons/favicon-64.png',
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js',
  'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js'
];

/* stale-while-revalidate: cached copy first, refresh in background */
const CDN_HOSTS = new Set([
  'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'tessdata.projectnaptha.com',
  'www.gstatic.com', 'fonts.googleapis.com', 'fonts.gstatic.com'
]);

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    /* per-file: one flaky CDN file must not break the install */
    await Promise.allSettled(PRECACHE.map(u => cache.add(new Request(u, { cache: 'reload' }))));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => !k.startsWith(VERSION)).map(k => caches.delete(k)));
    /* cache the pages that are already open: the very first navigation
       cannot be intercepted (no SW yet), so the page URL would otherwise
       never reach the cache and the first offline reload would 503. */
    const cache = await caches.open(SHELL);
    const open = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
    await Promise.allSettled(open.map(c => {
      const u = new URL(c.url);
      return (u.origin === self.location.origin)
        ? cache.add(new Request(u.href, { cache: 'reload' }))
        : null;
    }));
    await self.clients.claim();
  })());
});

self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });

async function swr(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const refresh = fetch(request).then(res => {
    if (res && (res.ok || res.type === 'opaque')) cache.put(request, res.clone());
    return res;
  }).catch(() => null);
  return cached || (await refresh) || Response.error();
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  /* Firebase APIs: never cached — AI calls and auth go to network only */
  if (url.hostname.endsWith('googleapis.com') || url.hostname.endsWith('cloudfunctions.net')) return;

  /* navigations: cached shell first (instant, offline-proof), refresh behind.
     Note: a navigate-mode Request cannot be re-fetched — re-fetch by URL. */
  if (req.mode === 'navigate') {
    e.respondWith((async () => {
      const cache = await caches.open(SHELL);
      const cached = (await cache.match(req.url))
                  || (await cache.match('./index.html'))
                  || (await cache.match('./'));
      if (cached) {
        fetch(new Request(req.url, { cache: 'reload' }))
          .then(r => r.ok && cache.put(req.url, r.clone())).catch(() => {});
        return cached;
      }
      try {
        const res = await fetch(new Request(req.url, { cache: 'reload' }));
        if (res.ok) cache.put(req.url, res.clone());
        return res;
      } catch (err) {
        return new Response('<h1 style="font-family:sans-serif">Redline is offline and this page was not cached yet — reconnect once, then it works in airplane mode.</h1>',
          { headers: { 'Content-Type': 'text/html' }, status: 503 });
      }
    })());
    return;
  }

  /* same-origin assets (icons, manifest, hosted html): cache-first + put */
  if (url.origin === self.location.origin) {
    e.respondWith((async () => {
      const cache = await caches.open(SHELL);
      const cached = await cache.match(req.url);
      if (cached) return cached;
      try {
        const res = await fetch(req);
        if (res.ok) cache.put(req.url, res.clone());
        return res;
      } catch (err) { return Response.error(); }
    })());
    return;
  }

  /* cross-origin CDN libs + tesseract assets: stale-while-revalidate */
  if (CDN_HOSTS.has(url.hostname)) {
    e.respondWith(swr(req, RUNTIME));
  }
});
