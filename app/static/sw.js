// Service Worker for SGK Export Application

const CACHE_NAME = 'sgk-cache-v2';
const API_CACHE_NAME = 'sgk-api-cache-v1';
const OFFLINE_FALLBACK_PAGE = '/offline.html';

// App shell files to cache during install
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
  '/static/js/modules/offline.js',
  '/static/js/modules/offline-form.js',
  '/static/js/modules/offline-navigation.js',
  '/static/js/modules/api-service.js',
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
  OFFLINE_FALLBACK_PAGE,
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://code.jquery.com/jquery-3.6.0.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
];

// URL patterns for pages to cache on visit
const PAGES_TO_CACHE = [
  /^\/$/, // Home page
  /^\/shipments\/$/, // Shipments list
  /^\/shipments\/new\/$/, // New shipment form
  /^\/profile\/$/, // Profile page
  /^\/docs\/$/, // Docs page
  /^\/login\/$/, // Login page
  /^\/register\/$/ // Register page
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
  const currentCaches = [CACHE_NAME, API_CACHE_NAME];
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

// Helper function to check if URL matches patterns
const matchesPatterns = (url, patterns) => {
  const pathname = new URL(url).pathname;
  return patterns.some(pattern => {
    if (pattern instanceof RegExp) {
      return pattern.test(pathname);
    }
    return pathname.includes(pattern);
  });
};

// Cache-first strategy for static assets
const cacheFirst = async (request) => {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    // Cache successful responses
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[Service Worker] Cache first fetch failed:', error);
    // No fallback for static assets
    throw error;
  }
};

// Stale-while-revalidate strategy for content
const staleWhileRevalidate = async (request) => {
  const cache = await caches.open(CACHE_NAME);
  
  // Try to get from cache
  const cachedResponse = await cache.match(request);
  
  // Fetch from network in background to update cache
  const networkResponsePromise = fetch(request).then(response => {
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    console.error('[Service Worker] Stale-while-revalidate fetch failed:', error);
    // Return null so we can handle the error later
    return null;
  });
  
  // Return cached response immediately or wait for network
  return cachedResponse || networkResponsePromise.then(networkResponse => {
    if (networkResponse) {
      return networkResponse;
    }
    // If both cache and network fail, return offline page for HTML requests
    if (request.headers.get('Accept').includes('text/html')) {
      return caches.match(OFFLINE_FALLBACK_PAGE);
    }
    throw new Error('Both cache and network failed');
  });
};

// Network-first strategy for dynamic content
const networkFirst = async (request) => {
  try {
    const response = await fetch(request);
    
    // Cache successful responses
    if (response && response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[Service Worker] Network-first fetch failed:', error);
    
    // Try to get from cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If this is a navigation, return offline page
    if (request.mode === 'navigate' || request.headers.get('Accept').includes('text/html')) {
      return caches.match(OFFLINE_FALLBACK_PAGE);
    }
    
    throw error;
  }
};

// Special handling for API requests - network with cache fallback + JSON response when offline
const apiStrategy = async (request) => {
  const cache = await caches.open(API_CACHE_NAME);
  
  try {
    // Try network first for API requests
    const response = await fetch(request);
    
    // Cache successful API responses
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[Service Worker] API fetch failed:', error);
    
    // Try to get from cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      // Add header to indicate this is from cache
      const clonedResponse = cachedResponse.clone();
      const bodyPromise = clonedResponse.json();
      
      return bodyPromise.then(data => {
        // Add a field to indicate this is cached data
        data.isCached = true;
        data.cachedAt = new Date().toISOString();
        
        return new Response(JSON.stringify(data), {
          headers: {
            'Content-Type': 'application/json',
            'X-Is-Cached': 'true'
          },
          status: 200
        });
      });
    }
    
    // If no cached data, return a JSON response indicating offline status
    return new Response(JSON.stringify({
      error: 'You are currently offline.',
      offline: true,
      endpoint: request.url,
      timestamp: new Date().toISOString()
    }), {
      headers: {
        'Content-Type': 'application/json',
        'X-Is-Offline': 'true'
      },
      status: 503 // Service Unavailable
    });
  }
};

// Page caching strategy - cache important pages when visited
const cachePageOnVisit = async (request, response) => {
  if (response && response.status === 200) {
    const url = new URL(request.url);
    
    // Check if this page should be cached
    if (matchesPatterns(url.toString(), PAGES_TO_CACHE)) {
      console.log('[Service Worker] Caching important page:', url.pathname);
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
  }
  return response;
};

// Fetch event - apply different strategies based on request type
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests and opaque cross-origin requests that we can't cache properly
  if (request.method !== 'GET' || 
      (!url.origin.includes(self.location.origin) && 
       !url.hostname.includes('cdn.jsdelivr.net') && 
       !url.hostname.includes('cdnjs.cloudflare.com') && 
       !url.hostname.includes('code.jquery.com'))) {
    return;
  }
  
  // HTML navigation requests - network first with offline fallback
  if (request.mode === 'navigate' || 
      (request.method === 'GET' && request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      networkFirst(request)
        .then(response => cachePageOnVisit(request, response))
    );
    return;
  }
  
  // API requests - special handling with cache fallback and offline JSON response
  if (url.pathname.includes('/api/')) {
    event.respondWith(apiStrategy(request));
    return;
  }
  
  // Static assets (CSS, JS, images, fonts) - cache first
  if (url.pathname.endsWith('.css') || 
      url.pathname.endsWith('.js') || 
      url.pathname.endsWith('.png') || 
      url.pathname.endsWith('.jpg') || 
      url.pathname.endsWith('.jpeg') || 
      url.pathname.endsWith('.svg') || 
      url.pathname.endsWith('.gif') ||
      url.pathname.endsWith('.woff') ||
      url.pathname.endsWith('.woff2') ||
      url.pathname.endsWith('.ttf') ||
      url.pathname.includes('/static/')) {
    event.respondWith(cacheFirst(request));
    return;
  }
  
  // Default - stale while revalidate
  event.respondWith(staleWhileRevalidate(request));
});

// Handle messages from the main thread
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  // Handle app version updates
  if (event.data && event.data.type === 'CHECK_VERSION') {
    const currentVersion = event.data.version;
    // Send current version to all clients
    clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.postMessage({
          type: 'VERSION_STATUS',
          version: currentVersion,
          // Logic to determine if update is needed would go here
          needsUpdate: false
        });
      });
    });
  }
  
  // Handle cache page request - manually cache a specific page
  if (event.data && event.data.type === 'CACHE_PAGE') {
    const urlToCache = event.data.url || self.location.origin + '/';
    console.log('[Service Worker] Manual request to cache page:', urlToCache);
    
    caches.open(CACHE_NAME).then(cache => {
      fetch(urlToCache).then(response => {
        if (response.status === 200) {
          cache.put(urlToCache, response.clone());
          console.log('[Service Worker] Page cached successfully:', urlToCache);
          
          // Notify client that page was cached
          event.source.postMessage({
            type: 'PAGE_CACHED',
            url: urlToCache,
            success: true
          });
        } else {
          console.error('[Service Worker] Failed to cache page, status:', response.status);
          event.source.postMessage({
            type: 'PAGE_CACHED',
            url: urlToCache,
            success: false,
            error: `Failed to cache page, status: ${response.status}`
          });
        }
      }).catch(error => {
        console.error('[Service Worker] Error caching page:', error);
        event.source.postMessage({
          type: 'PAGE_CACHED',
          url: urlToCache,
          success: false,
          error: error.message
        });
      });
    });
  }
  
  // Handle clear cache request
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    console.log('[Service Worker] Request to clear cache');
    
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('[Service Worker] Caches cleared successfully');
      
      // Re-cache app shell
      caches.open(CACHE_NAME).then(cache => {
        return cache.addAll(APP_SHELL);
      }).then(() => {
        console.log('[Service Worker] App shell re-cached');
        
        // Notify client that cache was cleared
        event.source.postMessage({
          type: 'CACHE_CLEARED',
          success: true
        });
      });
    }).catch(error => {
      console.error('[Service Worker] Error clearing caches:', error);
      event.source.postMessage({
        type: 'CACHE_CLEARED',
        success: false,
        error: error.message
      });
    });
  }
});

// Background sync for offline form submissions
self.addEventListener('sync', event => {
  if (event.tag === 'form-sync') {
    console.log('[Service Worker] Background sync event triggered');
    
    event.waitUntil(
      // This would be implemented client-side with the offline form module
      // The service worker just listens for the sync event
      clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage({
            type: 'SYNC_FORMS'
          });
        });
      })
    );
  }
}); 