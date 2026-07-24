const CACHE = "birdbrain-static-v2";
const STATIC = [
    "/",
    "/app.js",
    "/style.css",
    "/engine.js",
    "/manifest.json",
    "/icon-192.png",
    "/icon-512.png",
    "/birds.json",
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
