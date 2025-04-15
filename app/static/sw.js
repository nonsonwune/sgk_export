// Service Worker for SGK Export Application

const CACHE_NAME = 'sgk-cache-v1';
const APP_SHELL = [
  '/',
  '/static/css/main.css',
  '/static/css/critical.css',
  '/static/css/components/navigation.css',
  '/static/css/components/buttons.css',
  '/static/css/components/forms.css',
  '/static/css/components/tables.css',
  '/static/css/components/modals.css',
  '/static/css/components/footer.css',
  '/static/js/main.js',
  '/static/js/modules/navigation.js',
  '/static/js/modules/modal.js',
  '/static/js/modules/validation.js',
  '/static/manifest.json',
  '/static/images/SGKlogo.png',
  '/static/images/icons/icon-72x72.png',
  '/static/images/icons/icon-96x96.png',
  '/static/images/icons/icon-128x128.png',
  '/static/images/icons/icon-144x144.png',
  '/static/images/icons/icon-152x152.png',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-384x384.png',
  '/static/images/icons/icon-512x512.png',
  '/static/images/icons/maskable-icon.png',
  '/offline.html',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://code.jquery.com/jquery-3.6.0.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
];

// Install event - precache application shell
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching app shell');
        return cache.addAll(APP_SHELL);
      })
      .then(() => {
        console.log('[Service Worker] Skip waiting on install');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating');
  const currentCaches = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return cacheNames.filter(cacheName => !currentCaches.includes(cacheName));
    }).then(cachesToDelete => {
      return Promise.all(cachesToDelete.map(cacheToDelete => {
        console.log('[Service Worker] Deleting old cache:', cacheToDelete);
        return caches.delete(cacheToDelete);
      }));
    }).then(() => {
      console.log('[Service Worker] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Stale-while-revalidate strategy for content
const staleWhileRevalidate = (event, cacheName) => {
  return caches.open(cacheName).then(cache => {
    return cache.match(event.request).then(response => {
      const fetchPromise = fetch(event.request).then(networkResponse => {
        if (networkResponse && networkResponse.status === 200) {
          cache.put(event.request, networkResponse.clone());
        }
        return networkResponse;
      }).catch(error => {
        console.log('[Service Worker] Fetch failed; returning offline page instead.', error);
        return caches.match('/offline.html');
      });
      
      return response || fetchPromise;
    });
  });
};

// Network-first strategy for dynamic content
const networkFirst = (event, cacheName) => {
  return fetch(event.request)
    .then(response => {
      if (response && response.status === 200) {
        const responseToCache = response.clone();
        caches.open(cacheName).then(cache => {
          cache.put(event.request, responseToCache);
        });
      }
      return response;
    })
    .catch(() => {
      return caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        // If this is a navigation, return offline page
        if (event.request.mode === 'navigate') {
          return caches.match('/offline.html');
        }
        return null;
      });
    });
};

// Fetch event - apply different strategies based on request type
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests and cross-origin requests except known CDNs
  if (request.method !== 'GET' || 
      (!url.origin.includes(self.location.origin) && 
       !url.hostname.includes('cdn.jsdelivr.net') && 
       !url.hostname.includes('cdnjs.cloudflare.com') && 
       !url.hostname.includes('code.jquery.com'))) {
    return;
  }
  
  // HTML navigation requests - network first
  if (request.mode === 'navigate' || 
      (request.method === 'GET' && request.headers.get('accept').includes('text/html'))) {
    event.respondWith(networkFirst(event, CACHE_NAME));
    return;
  }
  
  // CSS, JavaScript, and Image assets - stale while revalidate
  if (url.pathname.endsWith('.css') || 
      url.pathname.endsWith('.js') || 
      url.pathname.endsWith('.png') || 
      url.pathname.endsWith('.jpg') || 
      url.pathname.endsWith('.jpeg') || 
      url.pathname.endsWith('.svg') || 
      url.pathname.endsWith('.gif') ||
      url.pathname.includes('/static/')) {
    event.respondWith(staleWhileRevalidate(event, CACHE_NAME));
    return;
  }
  
  // API requests - network only with offline fallback
  if (url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .catch(() => {
          return new Response(JSON.stringify({ 
            error: 'You are currently offline. Please try again when you have a network connection.' 
          }), {
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }
  
  // Default - stale while revalidate
  event.respondWith(staleWhileRevalidate(event, CACHE_NAME));
});

// Handle messages from the main thread
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  // Handle app version updates
  if (event.data && event.data.type === 'CHECK_VERSION') {
    const currentVersion = event.data.version;
    // Logic to check if there's a new version and prompt user to update
    clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.postMessage({
          type: 'VERSION_STATUS',
          version: currentVersion,
          needsUpdate: false // Logic to determine if update is needed
        });
      });
    });
  }
}); 