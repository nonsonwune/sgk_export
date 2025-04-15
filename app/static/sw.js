// Service Worker for SGK Export Application

const CACHE_NAME = 'sgk-cache-v1';
const STATIC_ASSETS = [
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
  '/static/images/SGKlogo.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://code.jquery.com/jquery-3.6.0.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const currentCaches = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return cacheNames.filter(cacheName => !currentCaches.includes(cacheName));
    }).then(cachesToDelete => {
      return Promise.all(cachesToDelete.map(cacheToDelete => {
        return caches.delete(cacheToDelete);
      }));
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  // Skip cross-origin requests, like those for Google Analytics
  if (event.request.url.startsWith(self.location.origin) || 
      event.request.url.includes('cdn.jsdelivr.net') ||
      event.request.url.includes('cdnjs.cloudflare.com') ||
      event.request.url.includes('code.jquery.com')) {
    
    // HTML documents - network first, fallback to cache
    if (event.request.headers.get('Accept').includes('text/html')) {
      event.respondWith(
        fetch(event.request)
          .then(response => {
            // If we got a valid response, cache it for offline use
            if (response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, responseClone);
              });
            }
            return response;
          })
          .catch(() => {
            // If the network is unavailable, get from cache
            return caches.match(event.request).then(cachedResponse => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // No cache match - show offline page
              return caches.match('/offline.html');
            });
          })
      );
      return;
    }
    
    // For static assets - cache first, fallback to network
    event.respondWith(
      caches.match(event.request)
        .then(cachedResponse => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          return fetch(event.request)
            .then(response => {
              // Don't cache responses that aren't successful
              if (!response || response.status !== 200 || response.type !== 'basic') {
                return response;
              }
              
              // Cache successful responses for future use
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then(cache => {
                  cache.put(event.request, responseToCache);
                });
                
              return response;
            });
        })
    );
  }
});

// Handle messages from the main thread
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
}); 