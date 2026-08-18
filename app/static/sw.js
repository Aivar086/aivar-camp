const CACHE_NAME = 'aivar-camp-v3-fresh';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Для запросов авторизации и страниц — всегда свежий запрос в сеть
  if (event.request.mode === 'navigate' || event.request.url.includes('/auth') || event.request.url.includes('/login')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  // Для статики — сеть с фолбэком в кеш
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
