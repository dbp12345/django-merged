const CACHE_NAME = "pwa_vehicle-db-cache-v2.1";
const urlsToCache = [
  "/pwa/login/",
  "/pwa/register/",
  "/pwa/vehicle_form/",
  "/static/pwa_vehicle/css/styles.css",
  "/static/pwa_vehicle/pwa/manifest.json",
  "/static/pwa_vehicle/pwa/icon.png",
  "/static/pwa_vehicle/js/qr-scanner.min.js",
  "/static/pwa_vehicle/js/qr-scanner-worker.min.js",
];

// Установка кеша и немедленная активация
self.addEventListener("install", function (event) {
  self.skipWaiting();  // немедленно активируем новый SW
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(urlsToCache);
    })
  );
});

// Активация и удаление старого кеша
self.addEventListener("activate", function (event) {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function (keyList) {
      return Promise.all(
        keyList.map(function (key) {
          if (!cacheWhitelist.includes(key)) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Отдаём кеш при запросах
self.addEventListener("fetch", function (event) {
  event.respondWith(
    caches.match(event.request).then(function (response) {
      // Если есть в кеше — отдаём
      if (response) {
        return response;
      }
      // Если нет — пробуем сеть и потом кешируем
      return fetch(event.request).then(function (networkResponse) {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
          return networkResponse;
        }
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      });
    }).catch(() => {
      // оффлайн-страница (если нужно)
    })
  );
});
