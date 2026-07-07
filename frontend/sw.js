const CACHE = "birdbrain-v2";
const STATIC = [
    "/",
    "/static/app.js?v=13",
    "/static/style.css?v=13",
    "/static/manifest.json",
    "/static/icon-192.svg",
    "/static/icon-512.svg",
    "/data/birds.json",
];

self.addEventListener("install", e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)));
    self.skipWaiting();
});

self.addEventListener("activate", e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", e => {
    const url = new URL(e.request.url);
    // API calls: network-only (never cache answers/progress)
    if (url.pathname.startsWith("/api/")) {
        e.respondWith(fetch(e.request));
        return;
    }
    // External media (Macaulay Library, Xeno-canto): network-only
    if (url.origin !== self.location.origin) {
        e.respondWith(fetch(e.request));
        return;
    }
    // Static assets: cache-first, fall back to network
    e.respondWith(
        caches.match(e.request).then(cached => cached || fetch(e.request))
    );
});
