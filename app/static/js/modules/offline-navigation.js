// Offline Navigation Module - Handles navigation when offline
import { OfflineManager, isOffline } from './offline.js';

export class OfflineNavigationManager {
    constructor() {
        this.initialized = false;
        this.availableOfflineRoutes = new Set();
        this.pendingNavigations = [];
        this.interceptedLinks = new WeakSet();
    }

    /**
     * Initialize the offline navigation manager
     */
    init() {
        if (this.initialized) return;
        
        // Check for cached pages first
        this.updateAvailableOfflineRoutes();
        
        // Set up link click interceptor
        this.setupLinkInterceptor();
        
        // Set up event listeners for online/offline
        OfflineManager.onOnline(() => this.handleOnline());
        OfflineManager.onOffline(() => this.handleOffline());
        
        // Handle initial state
        if (isOffline()) {
            this.handleOffline();
        }
        
        this.initialized = true;
        console.log('Offline Navigation Manager initialized');
    }

    /**
     * Find all cached pages that are available offline
     */
    async updateAvailableOfflineRoutes() {
        if ('caches' in window) {
            try {
                const cache = await caches.open('sgk-cache-v1');
                const requests = await cache.keys();
                
                this.availableOfflineRoutes.clear();
                
                // Add home page by default
                this.availableOfflineRoutes.add('/');
                
                requests.forEach(request => {
                    const url = new URL(request.url);
                    
                    // Only include HTML routes
                    if (url.pathname.endsWith('.html') || 
                        url.pathname === '/' || 
                        url.pathname.endsWith('/') ||
                        // Include any path that doesn't have a file extension (likely a route)
                        (!url.pathname.includes('.') && url.pathname !== '/sw.js')) {
                        this.availableOfflineRoutes.add(url.pathname);
                    }
                });
                
                console.log('Available offline routes:', [...this.availableOfflineRoutes]);
            } catch (error) {
                console.error('Error getting cached routes:', error);
            }
        }
    }

    /**
     * Handle online event
     */
    handleOnline() {
        // Process any pending navigations
        this.processPendingNavigations();
        
        // Update available offline routes
        this.updateAvailableOfflineRoutes();
    }

    /**
     * Handle offline event
     */
    handleOffline() {
        // Update UI to show we're offline
        document.body.classList.add('is-offline');
        
        // Update available offline routes
        this.updateAvailableOfflineRoutes();
    }

    /**
     * Process any pending navigations that were saved while offline
     */
    processPendingNavigations() {
        if (this.pendingNavigations.length === 0) return;
        
        console.log(`Processing ${this.pendingNavigations.length} pending navigations`);
        
        // Get the last navigation attempt (most recent intent)
        const lastNavigation = this.pendingNavigations.pop();
        
        // Clear the queue
        this.pendingNavigations = [];
        
        // Navigate to the last attempted URL
        if (lastNavigation && lastNavigation !== window.location.pathname) {
            console.log(`Navigating to pending URL: ${lastNavigation}`);
            window.location.href = lastNavigation;
        }
    }

    /**
     * Intercept link clicks to handle offline case
     */
    setupLinkInterceptor() {
        // Use event delegation for better performance
        document.addEventListener('click', (event) => {
            // Find closest anchor tag
            const link = event.target.closest('a');
            
            // If no link, or already intercepted, or has target, skip
            if (!link || this.interceptedLinks.has(link) || link.target || link.hasAttribute('download')) {
                return;
            }
            
            // Get the href
            const href = link.getAttribute('href');
            
            // Skip if no href, or it's a hash link, or an external link, or a special protocol
            if (!href || href.startsWith('#') || href.startsWith('http') || href.includes('://')) {
                return;
            }
            
            // Mark this link as intercepted
            this.interceptedLinks.add(link);
            
            // Add click handler
            link.addEventListener('click', (e) => this.handleLinkClick(e, link, href));
        });
    }

    /**
     * Handle link click with offline awareness
     * @param {Event} event - Click event
     * @param {HTMLAnchorElement} link - The clicked link
     * @param {string} href - The href value
     */
    handleLinkClick(event, link, href) {
        // If we're online, let the link work normally
        if (!isOffline()) return;
        
        // If we're offline, check if the route is available offline
        if (this.availableOfflineRoutes.has(href)) {
            // Route is available offline, let it proceed
            console.log(`Offline navigation to available route: ${href}`);
            return;
        }
        
        // Route is not available offline, prevent default
        event.preventDefault();
        
        // Add to pending navigations
        this.pendingNavigations.push(href);
        
        // Show message that this page isn't available offline
        this.showOfflineRouteUnavailable(href);
        
        console.log(`Attempted offline navigation to unavailable route: ${href}`);
    }

    /**
     * Show message that the route is not available offline
     * @param {string} route - The route that was attempted
     */
    showOfflineRouteUnavailable(route) {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('offline-route-notification');
        
        if (notification) {
            // If notification exists, update it
            const messageElement = notification.querySelector('.offline-route-message');
            if (messageElement) {
                messageElement.textContent = `The page "${this.getPageNameFromRoute(route)}" is not available offline.`;
            }
            notification.classList.remove('hidden');
        } else {
            // Create new notification
            notification = document.createElement('div');
            notification.id = 'offline-route-notification';
            notification.className = 'offline-route-notification';
            notification.innerHTML = `
                <div class="offline-notification-icon">⚠️</div>
                <div class="offline-notification-content">
                    <p class="offline-notification-title">Page Unavailable Offline</p>
                    <p class="offline-route-message">The page "${this.getPageNameFromRoute(route)}" is not available offline.</p>
                    <p class="offline-notification-help">This link will open when you're back online.</p>
                </div>
                <button class="offline-notification-close" aria-label="Close notification">✕</button>
            `;
            
            // Add styles if not already added
            if (!document.getElementById('offline-route-styles')) {
                const style = document.createElement('style');
                style.id = 'offline-route-styles';
                style.textContent = `
                    .offline-route-notification {
                        position: fixed;
                        top: 16px;
                        right: 16px;
                        background-color: #ff9800;
                        color: white;
                        padding: 12px 24px;
                        border-radius: 4px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                        display: flex;
                        align-items: center;
                        z-index: 9999;
                        transition: transform 0.3s ease, opacity 0.3s ease;
                        max-width: 90%;
                    }
                    .offline-route-notification.hidden {
                        transform: translateY(-100px);
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
                    .offline-route-message {
                        margin: 4px 0;
                        font-size: 14px;
                    }
                    .offline-notification-help {
                        margin: 4px 0 0 0;
                        font-size: 12px;
                        opacity: 0.9;
                    }
                    .offline-notification-close {
                        background: transparent;
                        border: none;
                        color: white;
                        cursor: pointer;
                        padding: 4px;
                        margin-left: auto;
                        font-size: 16px;
                        align-self: flex-start;
                    }
                    /* Styling for offline mode */
                    body.is-offline .online-only {
                        display: none !important;
                    }
                    body.is-offline .offline-only {
                        display: block !important;
                    }
                    body:not(.is-offline) .offline-only {
                        display: none !important;
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(notification);
            
            // Add close button functionality
            const closeButton = notification.querySelector('.offline-notification-close');
            closeButton.addEventListener('click', () => {
                notification.classList.add('hidden');
                // Remove after animation completes
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            });
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (notification && !notification.classList.contains('hidden')) {
                notification.classList.add('hidden');
                // Remove after animation completes
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    /**
     * Get a readable page name from a route
     * @param {string} route - Route path
     * @returns {string} - Human-readable page name
     */
    getPageNameFromRoute(route) {
        if (route === '/' || route === '') return 'Home';
        
        // Remove trailing slash if present
        const path = route.endsWith('/') ? route.slice(0, -1) : route;
        
        // Get the last segment of the path
        const lastSegment = path.split('/').pop() || '';
        
        // Convert to title case and replace hyphens with spaces
        return lastSegment
            .replace(/\.html$/, '')
            .replace(/-/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    }
}

// Create singleton instance
const offlineNavigationManager = new OfflineNavigationManager();

// Initialize the offline navigation manager
document.addEventListener('DOMContentLoaded', () => {
    offlineNavigationManager.init();
});

/**
 * Adds offline availability indicator to navigation links
 */
export function enhanceNavigationWithOfflineIndicators() {
    // Wait for offline navigation manager to be initialized
    const checkInterval = setInterval(() => {
        if (offlineNavigationManager.initialized) {
            clearInterval(checkInterval);
            updateOfflineIndicators();
        }
    }, 100);
    
    function updateOfflineIndicators() {
        // Add indicators to all nav links
        document.querySelectorAll('a').forEach(link => {
            // Skip external links, hash links, etc.
            const href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('http') || href.includes('://')) {
                return;
            }
            
            // Check if this route is available offline
            const isAvailableOffline = offlineNavigationManager.availableOfflineRoutes.has(href);
            
            // Remove any existing indicators
            link.querySelectorAll('.offline-indicator').forEach(el => el.remove());
            
            // Add appropriate indicator
            const indicator = document.createElement('span');
            indicator.className = `offline-indicator ${isAvailableOffline ? 'available' : 'unavailable'}`;
            indicator.innerHTML = isAvailableOffline ? '📶' : '';
            indicator.title = isAvailableOffline ? 'Available offline' : 'Not available offline';
            indicator.setAttribute('aria-hidden', 'true');
            
            // Only show indicator when offline
            if (isOffline()) {
                link.appendChild(indicator);
            }
            
            // Add style for indicators if not already added
            if (!document.getElementById('offline-indicators-style')) {
                const style = document.createElement('style');
                style.id = 'offline-indicators-style';
                style.textContent = `
                    .offline-indicator {
                        font-size: 0.6em;
                        margin-left: 4px;
                        vertical-align: super;
                    }
                    .offline-indicator.available {
                        color: #4CAF50;
                    }
                    .offline-indicator.unavailable {
                        color: #F44336;
                    }
                `;
                document.head.appendChild(style);
            }
        });
    }
    
    // Update indicators when online/offline status changes
    window.addEventListener('online', updateOfflineIndicators);
    window.addEventListener('offline', updateOfflineIndicators);
}

/**
 * Add current page to cache for offline access
 */
export function addCurrentPageToOfflineCache() {
    const cacheName = 'sgk-cache-v1';
    const currentUrl = window.location.pathname;
    
    // Only cache if online
    if (isOffline()) return;
    
    caches.open(cacheName).then(cache => {
        cache.add(currentUrl).then(() => {
            console.log(`Added ${currentUrl} to offline cache`);
            // Update available offline routes
            offlineNavigationManager.updateAvailableOfflineRoutes();
        }).catch(error => {
            console.error(`Failed to add ${currentUrl} to cache:`, error);
        });
    });
} 