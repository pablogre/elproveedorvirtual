// FactuFácil Móvil - Service Worker
// Cache simple de assets estáticos para que la app abra rápido y funcione offline básico
const CACHE_NAME = 'factufacil-mob-v1';
const ASSETS = [
  '/static/mob/icon-192.png',
  '/static/mob/icon-512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Solo cachear GET de assets estáticos. Las APIs siempre van a la red.
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET') return;
  if (url.pathname.startsWith('/mob/api/')) return;
  if (url.pathname.startsWith('/mob/login')) return;

  // Network-first para HTML, cache-first para assets
  if (url.pathname.startsWith('/static/') || url.hostname === 'cdnjs.cloudflare.com') {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request).then(resp => {
        const respClone = resp.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, respClone)).catch(() => {});
        return resp;
      }).catch(() => cached))
    );
  }
});
