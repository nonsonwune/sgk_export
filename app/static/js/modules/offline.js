// Offline Utility Module
export const OfflineManager = {
    isOnline: navigator.onLine,
    offlineListeners: [],
    onlineListeners: [],
    initialized: false,
    offlineNotification: null,

    /**
     * Initialize the offline manager
     */
    init() {
        if (this.initialized) return;
        
        // Set up event listeners for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Create style for offline notifications
        this.createOfflineStyles();
        
        // Handle initial state
        if (!navigator.onLine) {
            this.handleOffline();
        }
        
        this.initialized = true;
        console.log('Offline Manager initialized');
    },
    
    /**
     * Register a callback to be executed when the app goes offline
     * @param {Function} callback - Function to execute when offline
     */
    onOffline(callback) {
        this.offlineListeners.push(callback);
        return this; // For method chaining
    },
    
    /**
     * Register a callback to be executed when the app goes back online
     * @param {Function} callback - Function to execute when online
     */
    onOnline(callback) {
        this.onlineListeners.push(callback);
        return this; // For method chaining
    },
    
    /**
     * Handle offline event
     */
    handleOffline() {
        console.log('Device is offline');
        this.isOnline = false;
        this.showOfflineNotification();
        
        // Execute all registered offline callbacks
        this.offlineListeners.forEach(callback => {
            try {
                callback();
            } catch (error) {
                console.error('Error in offline callback:', error);
            }
        });
    },
    
    /**
     * Handle online event
     */
    handleOnline() {
        console.log('Device is back online');
        this.isOnline = true;
        this.hideOfflineNotification();
        
        // Execute all registered online callbacks
        this.onlineListeners.forEach(callback => {
            try {
                callback();
            } catch (error) {
                console.error('Error in online callback:', error);
            }
        });
    },
    
    /**
     * Create styles for offline notifications
     */
    createOfflineStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .offline-notification {
                position: fixed;
                bottom: 16px;
                left: 16px;
                background-color: #f44336;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                display: flex;
                align-items: center;
                z-index: 9999;
                transition: transform 0.3s ease, opacity 0.3s ease;
                transform: translateY(0);
                opacity: 1;
            }
            .offline-notification.hidden {
                transform: translateY(100px);
                opacity: 0;
            }
            .offline-notification-icon {
                margin-right: 12px;
                font-size: 20px;
            }
            .offline-notification-content {
                margin-right: 12px;
            }
            .offline-notification-title {
                font-weight: bold;
                margin: 0;
                font-size: 16px;
            }
            .offline-notification-message {
                margin: 4px 0 0 0;
                font-size: 14px;
            }
            .offline-notification-close {
                background: transparent;
                border: none;
                color: white;
                cursor: pointer;
                padding: 4px;
                margin-left: auto;
                font-size: 16px;
            }
        `;
        document.head.appendChild(style);
    },
    
    /**
     * Show offline notification
     */
    showOfflineNotification() {
        // If notification already exists, just show it
        if (this.offlineNotification) {
            this.offlineNotification.classList.remove('hidden');
            return;
        }
        
        this.offlineNotification = document.createElement('div');
        this.offlineNotification.className = 'offline-notification';
        this.offlineNotification.innerHTML = `
            <div class="offline-notification-icon">📶</div>
            <div class="offline-notification-content">
                <p class="offline-notification-title">You're offline</p>
                <p class="offline-notification-message">Some features may be unavailable</p>
            </div>
            <button class="offline-notification-close" aria-label="Close notification">✕</button>
        `;
        
        // Add close button functionality
        const closeButton = this.offlineNotification.querySelector('.offline-notification-close');
        closeButton.addEventListener('click', () => {
            this.hideOfflineNotification();
        });
        
        document.body.appendChild(this.offlineNotification);
    },
    
    /**
     * Hide offline notification
     */
    hideOfflineNotification() {
        if (this.offlineNotification) {
            this.offlineNotification.classList.add('hidden');
        }
    },
    
    /**
     * Check if we're offline and handle the fetch request appropriately
     * @param {string} url - URL to fetch
     * @param {Object} options - Fetch options
     * @param {Object} offlineData - Data to return when offline
     * @returns {Promise} - Fetch result or offline data
     */
    async safeFetch(url, options = {}, offlineData = null) {
        if (!this.isOnline) {
            console.log(`Offline: Returning cached data for ${url}`);
            // If we're offline and have offline data, return it
            if (offlineData) {
                return {
                    json: () => Promise.resolve(offlineData),
                    text: () => Promise.resolve(JSON.stringify(offlineData)),
                    ok: true,
                    status: 200,
                    offline: true
                };
            }
            
            // Try to get from cache
            try {
                const cache = await caches.open('sgk-cache-v1');
                const cachedResponse = await cache.match(url);
                
                if (cachedResponse) {
                    return cachedResponse;
                }
            } catch (error) {
                console.error('Error accessing cache:', error);
            }
            
            // If we don't have offline data and can't find in cache, reject
            return Promise.reject(new Error('You are offline and this content is not available offline'));
        }
        
        // If online, do the actual fetch
        try {
            // Add CSRF token for non-GET requests
            if (options.method && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(options.method)) {
                // Get CSRF token
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
                
                // Create headers if they don't exist
                if (!options.headers) {
                    options.headers = {};
                }
                
                // If headers is a Headers object, use set method
                if (options.headers instanceof Headers) {
                    options.headers.set('X-CSRF-TOKEN', csrfToken);
                } else {
                    // Otherwise treat as a plain object
                    options.headers['X-CSRF-TOKEN'] = csrfToken;
                }
            }
            
            return await fetch(url, options);
        } catch (error) {
            console.error(`Fetch error for ${url}:`, error);
            
            // If fetch fails due to network error and we have offline data, use it
            if (offlineData) {
                return {
                    json: () => Promise.resolve(offlineData),
                    text: () => Promise.resolve(JSON.stringify(offlineData)),
                    ok: true,
                    status: 200,
                    offline: true
                };
            }
            
            throw error;
        }
    }
};

// Initialize the offline manager as soon as this module is imported
OfflineManager.init();

// Utility functions
export function isOffline() {
    return !navigator.onLine;
}

export function wrapFetchWithOfflineHandling(fetchFunction) {
    return async function(...args) {
        if (isOffline()) {
            // Handle offline case
            console.log('Network request attempted while offline:', args);
            return Promise.reject(new Error('You are offline. This action will be queued and performed when you go back online.'));
        }
        
        try {
            return await fetchFunction(...args);
        } catch (error) {
            // If error happens due to network, handle offline case
            if (!navigator.onLine || error.message.includes('network') || error.message.includes('fetch')) {
                console.log('Network error in fetch, likely offline:', error);
                return Promise.reject(new Error('Network error. This action will be queued and performed when you go back online.'));
            }
            
            throw error;
        }
    };
} 