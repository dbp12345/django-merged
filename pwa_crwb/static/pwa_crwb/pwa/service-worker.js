const CACHE_NAME = "pwa_crwb-db-cache-v2.36";  // Увеличь версию при каждом обновлении
const urlsToCache = [
    "/crwb/login/",
    "/crwb/register/",
    "/crwb/dispatch/",
    "/crwb/crew/",
    "/crwb/mspa/",
    "/static/pwa_crwb/css/styles.css",
    "/static/pwa_crwb/pwa/manifest.json",
    "/static/pwa_crwb/pwa/icon.png",
];

// Установка кеша и немедленная активация нового Service Worker
self.addEventListener("install", function (event) {
    self.skipWaiting();  // мгновенная активация
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
    const req = event.request;
    const url = new URL(req.url);

    // 1) Только GET кэшируем
    if (req.method !== "GET") {
        event.respondWith(fetch(req));
        return;
    }

    // 2) Исключаем манифесты и крупные файлы по пути или расширению (network-only)
    const isManifestPath = url.pathname.startsWith("/dispatch/manifest/get/");
    const isBigFileExt = /\.(pdf|docx|doc|xls|xlsx)$/i.test(url.pathname);
    if (isManifestPath || isBigFileExt) {
        // если нужна авторизация — include, иначе можно опустить
        event.respondWith(
            fetch(req, {credentials: "include"}).catch(() => caches.match("/offline.html"))
        );
        return;
    }

    // 3) Обычный cache-first + runtime caching для остальных ресурсов
    event.respondWith(
        caches.match(req).then(function (cached) {
            if (cached) return cached;

            return fetch(req, {credentials: "include"}).then(function (networkResponse) {
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
                    return networkResponse;
                }

                // Опционально: ещё дополнительно не кэшируем по Content-Type
                const ct = networkResponse.headers.get("Content-Type") || "";
                if (/application\/pdf|application\/vnd\.openxmlformats-officedocument/i.test(ct)) {
                    return networkResponse;
                }

                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then(function (cache) {
                    cache.put(req, responseToCache);
                });

                return networkResponse;
            }).catch(() => caches.match("/offline.html"));
        })
    );
});
