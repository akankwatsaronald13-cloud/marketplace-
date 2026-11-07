// SingleSearching - Self-Updating SW - v2
const VERSION = 'v2-2026-11-07-01'; // <-- BUMP THIS every time you change app.py
const CACHE = 'singlesearching-' + VERSION;
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

// Install - save new version, then take over immediately
self.addEventListener('install', (e) => {
  console.log('[SW] Installing', VERSION);
  e.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting()) // Don't wait - activate now
  );
});

// Activate - DELETE all old caches, take control
self.addEventListener('activate', (e) => {
  console.log('[SW] Activating', VERSION);
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => {
        if (k !== CACHE) {
          console.log('[SW] Deleting old cache', k);
          return caches.delete(k);
        }
      }))
    ).then(() => self.clients.claim())
  );
});

// Fetch - SMART strategy
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // 1. HTML / API / Admin - NETWORK FIRST, always fresh
  // This is the fix: app.py pages NEVER come from old cache
  if (e.request.mode === 'navigate' || url.pathname.startsWith('/admin') || url.pathname.startsWith('/api') || e.request.headers.get('accept')?.includes('text/html')) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          // Save fresh copy for offline, but return fresh
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(e.request, copy));
          return res;
        })
        .catch(() => caches.match(e.request)) // Offline fallback
    );
    return;
  }

  // 2. Images / CSS / JS - CACHE FIRST, fast, but update in background
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const fetchPromise = fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((cache) => cache.put(e.request, copy));
        return res;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});

// Listen for "skipWaiting" message from page
self.addEventListener('message', (e) => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
});
