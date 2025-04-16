// API Service Module - Handles API requests with offline caching
import { OfflineManager } from './offline.js';

/**
 * API Service class to handle fetching data with offline support
 */
export class ApiService {
    constructor() {
        this.defaultCacheDuration = 3600000; // 1 hour in milliseconds
        this.apiCache = {};
    }

    /**
     * Fetch data from API with offline support
     * @param {string} url - The API endpoint URL
     * @param {Object} options - Fetch options
     * @param {Object} cacheOptions - Caching options
     * @returns {Promise<Object>} - Promise resolving to response data
     */
    async fetch(url, options = {}, cacheOptions = {}) {
        const {
            useCache = true,
            cacheDuration = this.defaultCacheDuration,
            forceRefresh = false,
            offlineData = null
        } = cacheOptions;
        
        // Check for cached data
        if (useCache && !forceRefresh) {
            const cachedData = this.getCachedData(url);
            if (cachedData) {
                return cachedData;
            }
        }
        
        try {
            // Use offline manager's safe fetch to handle offline case
            const response = await OfflineManager.safeFetch(url, options, offlineData);
            
            // Check if response was generated while offline
            if (response.offline) {
                return response.json();
            }
            
            // Process normal response
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            
            // Parse JSON response
            const data = await response.json();
            
            // Cache the response if caching is enabled
            if (useCache) {
                this.cacheData(url, data, cacheDuration);
            }
            
            return data;
        } catch (error) {
            console.error(`API fetch error for ${url}:`, error);
            
            // If we have offline data, use it
            if (offlineData) {
                console.log(`Using offline data for ${url}`);
                return offlineData;
            }
            
            // Try to get from IndexedDB cache
            const dbCache = await this.getFromIndexedDBCache(url);
            if (dbCache) {
                console.log(`Using IndexedDB cached data for ${url}`);
                return dbCache;
            }
            
            throw error;
        }
    }

    /**
     * Cache data in memory
     * @param {string} url - The API endpoint URL
     * @param {Object} data - The data to cache
     * @param {number} duration - Cache duration in milliseconds
     */
    cacheData(url, data, duration) {
        this.apiCache[url] = {
            data,
            timestamp: Date.now(),
            expiry: Date.now() + duration
        };
        
        // Also cache in IndexedDB for persistence
        this.saveToIndexedDBCache(url, data, duration);
        
        console.log(`Cached data for ${url} for ${duration}ms`);
    }

    /**
     * Get cached data if not expired
     * @param {string} url - The API endpoint URL
     * @returns {Object|null} - Cached data or null if expired/not found
     */
    getCachedData(url) {
        const cached = this.apiCache[url];
        
        if (cached && cached.expiry > Date.now()) {
            console.log(`Using cached data for ${url}`);
            return cached.data;
        }
        
        // Clean up expired cache
        if (cached) {
            delete this.apiCache[url];
        }
        
        return null;
    }

    /**
     * Save data to IndexedDB cache
     * @param {string} url - The API endpoint URL
     * @param {Object} data - The data to cache
     * @param {number} duration - Cache duration in milliseconds
     */
    async saveToIndexedDBCache(url, data, duration) {
        if (!('indexedDB' in window)) return;
        
        try {
            const db = await this.openDatabase();
            const transaction = db.transaction(['apiCache'], 'readwrite');
            const store = transaction.objectStore('apiCache');
            
            const item = {
                url,
                data,
                timestamp: Date.now(),
                expiry: Date.now() + duration
            };
            
            store.put(item);
            console.log(`Saved to IndexedDB cache: ${url}`);
        } catch (error) {
            console.error('Error saving to IndexedDB cache:', error);
        }
    }

    /**
     * Get data from IndexedDB cache
     * @param {string} url - The API endpoint URL
     * @returns {Promise<Object|null>} - Cached data or null if expired/not found
     */
    async getFromIndexedDBCache(url) {
        if (!('indexedDB' in window)) return null;
        
        try {
            const db = await this.openDatabase();
            const transaction = db.transaction(['apiCache'], 'readonly');
            const store = transaction.objectStore('apiCache');
            const request = store.get(url);
            
            return new Promise((resolve, reject) => {
                request.onsuccess = () => {
                    const cached = request.result;
                    
                    if (cached && cached.expiry > Date.now()) {
                        console.log(`Retrieved from IndexedDB cache: ${url}`);
                        resolve(cached.data);
                    } else {
                        // Clean up expired cache
                        if (cached) {
                            const deleteTransaction = db.transaction(['apiCache'], 'readwrite');
                            const deleteStore = deleteTransaction.objectStore('apiCache');
                            deleteStore.delete(url);
                            console.log(`Removed expired IndexedDB cache: ${url}`);
                        }
                        resolve(null);
                    }
                };
                
                request.onerror = () => {
                    console.error('Error getting from IndexedDB cache:', request.error);
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('Error accessing IndexedDB cache:', error);
            return null;
        }
    }

    /**
     * Open IndexedDB database
     * @returns {Promise<IDBDatabase>} - Database instance
     */
    openDatabase() {
        return new Promise((resolve, reject) => {
            if (!('indexedDB' in window)) {
                reject(new Error('IndexedDB not supported'));
                return;
            }
            
            const request = indexedDB.open('sgkApiCache', 1);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('apiCache')) {
                    const store = db.createObjectStore('apiCache', { keyPath: 'url' });
                    store.createIndex('expiry', 'expiry', { unique: false });
                    console.log('Created IndexedDB store for API cache');
                }
            };
            
            request.onsuccess = () => {
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error('Error opening IndexedDB:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Clear all cached data
     */
    clearCache() {
        this.apiCache = {};
        this.clearIndexedDBCache();
        console.log('Cleared API cache');
    }

    /**
     * Clear IndexedDB cache
     */
    async clearIndexedDBCache() {
        if (!('indexedDB' in window)) return;
        
        try {
            const db = await this.openDatabase();
            const transaction = db.transaction(['apiCache'], 'readwrite');
            const store = transaction.objectStore('apiCache');
            store.clear();
            console.log('Cleared IndexedDB API cache');
        } catch (error) {
            console.error('Error clearing IndexedDB cache:', error);
        }
    }

    /**
     * Clean up expired cache entries
     */
    async cleanupExpiredCache() {
        if (!('indexedDB' in window)) return;
        
        try {
            const db = await this.openDatabase();
            const transaction = db.transaction(['apiCache'], 'readwrite');
            const store = transaction.objectStore('apiCache');
            const index = store.index('expiry');
            
            const now = Date.now();
            const range = IDBKeyRange.upperBound(now);
            
            const request = index.openCursor(range);
            
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    store.delete(cursor.primaryKey);
                    console.log(`Cleaned up expired cache: ${cursor.primaryKey}`);
                    cursor.continue();
                }
            };
            
            console.log('Completed cache cleanup');
        } catch (error) {
            console.error('Error during cache cleanup:', error);
        }
    }
}

// Create singleton instance
const apiService = new ApiService();

// Export default instance
export default apiService;

// Run cleanup periodically
setInterval(() => {
    apiService.cleanupExpiredCache();
}, 3600000); // Cleanup every hour 