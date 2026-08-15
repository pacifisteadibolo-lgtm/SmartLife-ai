// SmartLife AI — service worker : notifications push
// Tourne en arrière-plan, indépendamment de l'onglet ouvert ou non.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let donnees = { titre: 'SmartLife AI', corps: 'Nouveau message', url: '/messagerie/', tag: 'message' };
  try {
    if (event.data) donnees = { ...donnees, ...event.data.json() };
  } catch (e) { /* payload non-JSON, on garde les valeurs par défaut */ }

  const options = {
    body: donnees.corps,
    icon: '/static/img/icone-notification.png',
    badge: '/static/img/icone-notification.png',
    tag: donnees.tag,
    data: { url: donnees.url },
    // Le son par défaut du système est joué automatiquement par le navigateur/OS
    // à l'affichage d'une notification — c'est la "sonnerie" demandée.
    vibrate: [200, 100, 200],
    renotify: true,
  };

  event.waitUntil(self.registration.showNotification(donnees.titre, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/messagerie/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(url) && 'focus' in client) return client.focus();
      }
      if (clientList.length > 0 && 'focus' in clientList[0]) {
        clientList[0].navigate(url);
        return clientList[0].focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
