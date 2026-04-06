// Service Worker for Notifications PWA
const CACHE_NAME = 'notifications-pwa-v1.40';
const urlsToCache = [
  '/notifications/',
  '/static/notifications/pwa/icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});

self.addEventListener('push', async (event) => {
  console.log('[SW] Push event received:', event);
  
  let data = {};
  try {
    if (event.data) {
      data = event.data.json();
      console.log('[SW] Push data parsed:', data);
    } else {
      console.warn('[SW] Push event has no data');
      data = { head: 'Notification', body: 'You have a new notification' };
    }
  } catch (e) {
    console.error('[SW] Error parsing push data:', e);
    data = { head: 'Notification', body: 'You have a new notification' };
  }

  const options = {
    body: data.body || '',
    icon: data.icon || '/static/notifications/pwa/icon.png',
    badge: '/static/notifications/pwa/icon.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/notifications/'
    },
    requireInteraction: false,
    silent: false
  };

  // Notify all clients about new notification
  const clients = await self.clients.matchAll();
  console.log('[SW] Notifying', clients.length, 'clients');
  clients.forEach(client => {
    client.postMessage({ type: 'NOTIFICATION_RECEIVED' }).catch(e => {
      console.error('[SW] Error sending message to client:', e);
    });
  });

  try {
    const notification = await self.registration.showNotification(data.head || 'Notification', options);
    console.log('[SW] Notification shown successfully:', notification);
  } catch (e) {
    console.error('[SW] Error showing notification:', e);
    // Try without vibrate for iOS
    delete options.vibrate;
    try {
      await self.registration.showNotification(data.head || 'Notification', options);
      console.log('[SW] Notification shown without vibrate');
    } catch (e2) {
      console.error('[SW] Error showing notification (retry):', e2);
    }
  }
});

self.addEventListener('notificationclick', async (event) => {
  event.notification.close();
  
  // Notify clients
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({ type: 'CLEAR_NOTIFICATIONS' });
  });
  
  const url = event.notification.data && event.notification.data.url ? event.notification.data.url : '/notifications/';
  event.waitUntil(clients.openWindow(url));
});
