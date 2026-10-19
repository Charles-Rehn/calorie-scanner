// Opens instantly from the saved copy, then quietly fetches any update in the
// background so the next launch has it.
const CACHE = "calorie-scanner-v19";
const SHELL = ["./", "./index.html", "./config.js", "./manifest.webmanifest", "./icon-180.png", "./icon-192.png", "./icon-512.png", "./foods.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Never cache food lookups, the AI or the family database.
  if (/openfoodfacts|firestore|googleapis\.com\/identitytoolkit|securetoken|firebasevertexai|firebaseappcheck|recaptcha|google\.com/.test(url.href)) return;
  const sameOrigin = url.origin === self.location.origin;
  const cdn = /cdn\.jsdelivr\.net|gstatic\.com\/firebasejs|fonts\.(googleapis|gstatic)\.com/.test(url.href);
  if (!sameOrigin && !cdn) return;
  if (cdn) {
    // Versioned library files and fonts never change: cache first.
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    })));
    return;
  }
  // The app itself: answer from the saved copy straight away, refresh it in the background.
  const key = url.pathname.endsWith("/") ? new Request(new URL("./index.html", self.registration.scope)) : req;
  const fresh = fetch(req, { cache: "no-cache" }).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(key, copy)); }
    return res;
  });
  e.waitUntil(fresh.catch(() => {}));
  e.respondWith(caches.match(key, { ignoreSearch: true }).then(hit => hit || fresh.catch(() => caches.match("./index.html"))));
});
