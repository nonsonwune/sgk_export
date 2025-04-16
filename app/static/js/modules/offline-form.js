// Offline Form Module - Handles storing and submitting forms when offline
import { OfflineManager, isOffline } from './offline.js';

// IndexedDB setup for offline form storage
export class OfflineFormManager {
    constructor() {
        this.dbName = 'sgkOfflineDB';
        this.dbVersion = 1;
        this.storeName = 'pendingRequests';
        this.db = null;
        this.initialized = false;
        this.syncing = false;
    }

    /**
     * Initialize the database
     * @returns {Promise} - Promise that resolves when DB is ready
     */
    async init() {
        if (this.initialized) return this.db;

        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = (event) => {
                console.error('IndexedDB error:', event.target.error);
                reject(event.target.error);
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                this.initialized = true;
                console.log('OfflineFormManager: IndexedDB opened successfully');
                
                // Set up event listeners for online/offline
                OfflineManager.onOnline(() => this.syncPendingRequests());
                
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object store for pending requests
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, { keyPath: 'id', autoIncrement: true });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                    store.createIndex('url', 'url', { unique: false });
                    store.createIndex('synced', 'synced', { unique: false });
                    console.log('OfflineFormManager: Created object store for pending requests');
                }
            };
        });
    }

    /**
     * Save a form request to be processed when back online
     * @param {string} url - The API endpoint URL
     * @param {string} method - HTTP method (POST, PUT, etc)
     * @param {Object} data - Form data to be sent
     * @param {string} formId - Optional ID of the form
     * @returns {Promise} - Promise with the saved request ID
     */
    async saveRequest(url, method, data, formId = null) {
        await this.init();

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                
                const request = {
                    url,
                    method,
                    data,
                    formId,
                    timestamp: new Date().getTime(),
                    synced: false,
                    attempts: 0
                };
                
                const saveRequest = store.add(request);
                
                saveRequest.onsuccess = (event) => {
                    console.log('OfflineFormManager: Request saved with ID:', event.target.result);
                    resolve(event.target.result);
                };
                
                saveRequest.onerror = (event) => {
                    console.error('OfflineFormManager: Error saving request:', event.target.error);
                    reject(event.target.error);
                };
                
                transaction.oncomplete = () => {
                    console.log('OfflineFormManager: Transaction completed');
                    this.updateUI();
                };
            } catch (error) {
                console.error('OfflineFormManager: Error in saveRequest:', error);
                reject(error);
            }
        });
    }

    /**
     * Get all pending requests
     * @returns {Promise<Array>} - Promise with all pending requests
     */
    async getPendingRequests() {
        await this.init();

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readonly');
                const store = transaction.objectStore(this.storeName);
                const index = store.index('synced');
                
                const request = index.getAll(false);
                
                request.onsuccess = () => {
                    resolve(request.result);
                };
                
                request.onerror = (event) => {
                    console.error('OfflineFormManager: Error getting pending requests:', event.target.error);
                    reject(event.target.error);
                };
            } catch (error) {
                console.error('OfflineFormManager: Error in getPendingRequests:', error);
                reject(error);
            }
        });
    }

    /**
     * Mark a request as synced
     * @param {number} id - Request ID
     * @returns {Promise} - Promise that resolves when the request is marked as synced
     */
    async markRequestSynced(id) {
        await this.init();

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                
                const getRequest = store.get(id);
                
                getRequest.onsuccess = () => {
                    const data = getRequest.result;
                    if (!data) {
                        reject(new Error(`Request with ID ${id} not found`));
                        return;
                    }
                    
                    data.synced = true;
                    data.syncedAt = new Date().getTime();
                    
                    const updateRequest = store.put(data);
                    
                    updateRequest.onsuccess = () => {
                        resolve();
                    };
                    
                    updateRequest.onerror = (event) => {
                        console.error('OfflineFormManager: Error updating request:', event.target.error);
                        reject(event.target.error);
                    };
                };
                
                getRequest.onerror = (event) => {
                    console.error('OfflineFormManager: Error getting request:', event.target.error);
                    reject(event.target.error);
                };
                
                transaction.oncomplete = () => {
                    console.log(`OfflineFormManager: Request ${id} marked as synced`);
                    this.updateUI();
                };
            } catch (error) {
                console.error('OfflineFormManager: Error in markRequestSynced:', error);
                reject(error);
            }
        });
    }

    /**
     * Update request with new attempt count
     * @param {number} id - Request ID
     * @returns {Promise} - Promise that resolves when the request is updated
     */
    async updateRequestAttempt(id) {
        await this.init();

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                
                const getRequest = store.get(id);
                
                getRequest.onsuccess = () => {
                    const data = getRequest.result;
                    if (!data) {
                        reject(new Error(`Request with ID ${id} not found`));
                        return;
                    }
                    
                    data.attempts += 1;
                    data.lastAttempt = new Date().getTime();
                    
                    const updateRequest = store.put(data);
                    
                    updateRequest.onsuccess = () => {
                        resolve(data);
                    };
                    
                    updateRequest.onerror = (event) => {
                        console.error('OfflineFormManager: Error updating request attempt:', event.target.error);
                        reject(event.target.error);
                    };
                };
                
                getRequest.onerror = (event) => {
                    console.error('OfflineFormManager: Error getting request:', event.target.error);
                    reject(event.target.error);
                };
            } catch (error) {
                console.error('OfflineFormManager: Error in updateRequestAttempt:', error);
                reject(error);
            }
        });
    }

    /**
     * Sync all pending requests
     * @returns {Promise} - Promise that resolves when all requests are synced
     */
    async syncPendingRequests() {
        if (this.syncing || isOffline()) return;
        
        try {
            this.syncing = true;
            console.log('OfflineFormManager: Starting to sync pending requests');
            
            const pendingRequests = await this.getPendingRequests();
            console.log(`OfflineFormManager: Found ${pendingRequests.length} pending requests`);
            
            if (pendingRequests.length === 0) {
                this.syncing = false;
                return;
            }
            
            // Show syncing notification
            this.showSyncingNotification(pendingRequests.length);
            
            // Process requests in sequence
            let successCount = 0;
            for (const request of pendingRequests) {
                try {
                    await this.updateRequestAttempt(request.id);
                    
                    // Get CSRF token
                    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
                    
                    const response = await fetch(request.url, {
                        method: request.method,
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Was-Offline': 'true',
                            'X-CSRF-TOKEN': csrfToken
                        },
                        body: JSON.stringify(request.data)
                    });
                    
                    if (response.ok) {
                        await this.markRequestSynced(request.id);
                        successCount++;
                        this.updateSyncingNotification(pendingRequests.length, successCount);
                    } else {
                        console.error(`OfflineFormManager: Failed to sync request ${request.id}: ${response.status} ${response.statusText}`);
                        
                        // If server returns an unrecoverable error, mark as synced to prevent further attempts
                        if (response.status >= 400 && response.status < 500) {
                            await this.markRequestSynced(request.id);
                        }
                    }
                } catch (error) {
                    console.error(`OfflineFormManager: Error syncing request ${request.id}:`, error);
                }
            }
            
            // Hide syncing notification
            this.hideSyncingNotification(successCount, pendingRequests.length);
            
            console.log(`OfflineFormManager: Completed syncing. ${successCount}/${pendingRequests.length} succeeded.`);
        } catch (error) {
            console.error('OfflineFormManager: Error in syncPendingRequests:', error);
        } finally {
            this.syncing = false;
            this.updateUI();
        }
    }

    /**
     * Update UI elements to show pending requests
     */
    updateUI() {
        // Update UI badge or indicator if there are pending requests
        this.getPendingRequests().then(requests => {
            const badge = document.getElementById('offline-pending-badge');
            
            if (badge) {
                if (requests.length > 0) {
                    badge.textContent = requests.length;
                    badge.classList.remove('hidden');
                } else {
                    badge.classList.add('hidden');
                }
            }
        });
    }

    /**
     * Show notification that syncing is in progress
     * @param {number} total - Total number of requests to sync
     */
    showSyncingNotification(total) {
        let notification = document.getElementById('sync-notification');
        
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'sync-notification';
            notification.className = 'sync-notification';
            notification.innerHTML = `
                <div class="sync-notification-icon">🔄</div>
                <div class="sync-notification-content">
                    <p class="sync-notification-title">Syncing Data</p>
                    <p class="sync-notification-message">Uploading <span id="sync-progress">0</span>/${total} pending requests</p>
                </div>
            `;
            
            // Add styles if not already added
            if (!document.getElementById('sync-notification-styles')) {
                const style = document.createElement('style');
                style.id = 'sync-notification-styles';
                style.textContent = `
                    .sync-notification {
                        position: fixed;
                        top: 16px;
                        right: 16px;
                        background-color: #4169E1;
                        color: white;
                        padding: 12px 24px;
                        border-radius: 4px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                        display: flex;
                        align-items: center;
                        z-index: 9999;
                        transition: transform 0.3s ease, opacity 0.3s ease;
                    }
                    .sync-notification-icon {
                        margin-right: 12px;
                        font-size: 20px;
                        animation: spin 1.5s linear infinite;
                    }
                    @keyframes spin {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                    .sync-notification-content {
                        margin-right: 12px;
                    }
                    .sync-notification-title {
                        font-weight: bold;
                        margin: 0;
                        font-size: 16px;
                    }
                    .sync-notification-message {
                        margin: 4px 0 0 0;
                        font-size: 14px;
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(notification);
        }
    }

    /**
     * Update syncing notification with progress
     * @param {number} total - Total number of requests
     * @param {number} progress - Number of requests processed
     */
    updateSyncingNotification(total, progress) {
        const progressElement = document.getElementById('sync-progress');
        if (progressElement) {
            progressElement.textContent = progress;
        }
    }

    /**
     * Hide syncing notification and show completion notification
     * @param {number} success - Number of successful syncs
     * @param {number} total - Total number of requests
     */
    hideSyncingNotification(success, total) {
        const notification = document.getElementById('sync-notification');
        if (notification) {
            notification.remove();
        }
        
        // Show completion notification
        const completionNotification = document.createElement('div');
        completionNotification.className = 'sync-completion-notification';
        completionNotification.innerHTML = `
            <div class="sync-notification-icon">✅</div>
            <div class="sync-notification-content">
                <p class="sync-notification-title">Sync Complete</p>
                <p class="sync-notification-message">Successfully synced ${success} of ${total} requests</p>
            </div>
            <button class="sync-notification-close" aria-label="Close notification">✕</button>
        `;
        
        // Add styles if not already added
        if (!document.getElementById('sync-completion-styles')) {
            const style = document.createElement('style');
            style.id = 'sync-completion-styles';
            style.textContent = `
                .sync-completion-notification {
                    position: fixed;
                    top: 16px;
                    right: 16px;
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 4px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                    display: flex;
                    align-items: center;
                    z-index: 9999;
                    transition: transform 0.3s ease, opacity 0.3s ease;
                }
                .sync-notification-close {
                    background: transparent;
                    border: none;
                    color: white;
                    cursor: pointer;
                    padding: 4px;
                    margin-left: 12px;
                    font-size: 16px;
                }
                .sync-completion-notification .sync-notification-icon {
                    animation: none;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(completionNotification);
        
        // Add close button functionality
        const closeButton = completionNotification.querySelector('.sync-notification-close');
        closeButton.addEventListener('click', () => {
            completionNotification.remove();
        });
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (document.body.contains(completionNotification)) {
                completionNotification.remove();
            }
        }, 5000);
    }
}

// Create a singleton instance
const offlineFormManager = new OfflineFormManager();

/**
 * Enhance a form with offline capabilities
 * @param {HTMLFormElement} form - The form element to enhance
 * @param {Object} options - Options for the offline form
 */
export function enhanceFormWithOfflineSupport(form, options = {}) {
    if (!form) return;
    
    // Explicitly check if this form should be skipped
    if (form.hasAttribute('data-no-offline')) {
        console.log('Skipping offline enhancement for form due to data-no-offline attribute:', form.id || form.action);
        return;
    }
    
    const {
        formId = form.id || `form-${Math.random().toString(36).substr(2, 9)}`,
        endpoint = form.action,
        method = form.method.toUpperCase() || 'POST',
        successMessage = 'Form submitted successfully',
        offlineMessage = 'You are offline. This form will be submitted when you reconnect.',
        onSuccess = null,
        onOffline = null,
        transformData = null
    } = options;
    
    // Initialize the offline form manager
    offlineFormManager.init().catch(error => {
        console.error('Failed to initialize OfflineFormManager:', error);
    });
    
    // Store the original submit handler
    const originalSubmit = form.onsubmit;
    
    // Replace with our enhanced handler
    form.onsubmit = async function(event) {
        event.preventDefault();
        
        // If there's an original submit handler, call it
        if (originalSubmit && typeof originalSubmit === 'function') {
            const result = originalSubmit.call(this, event);
            // If the handler returns false, stop processing
            if (result === false) return false;
        }
        
        // Get form data
        const formData = new FormData(form);
        
        // Transform data if needed
        let data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });
        
        if (transformData && typeof transformData === 'function') {
            data = transformData(data);
        }
        
        // Check if we're offline
        if (isOffline()) {
            console.log('OfflineFormManager: Saving form submission for later:', formId);
            
            try {
                await offlineFormManager.saveRequest(endpoint, method, data, formId);
                
                // Show offline message
                showFormMessage(form, offlineMessage, 'info');
                
                // Call the offline callback if provided
                if (onOffline && typeof onOffline === 'function') {
                    onOffline(data);
                }
                
                // You might want to reset the form here depending on the use case
                // form.reset();
                
                return false;
            } catch (error) {
                console.error('OfflineFormManager: Error saving form submission:', error);
                showFormMessage(form, 'Error saving form data for offline submission', 'error');
                return false;
            }
        }
        
        // If we're online, submit normally
        try {
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            
            const response = await fetch(endpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': csrfToken
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                // Check if the response is a redirect
                if (response.redirected) {
                    // Handle redirect
                    window.location.href = response.url;
                    return false;
                }
                
                // Check content type to determine if it's JSON
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    // It's JSON, parse it
                    const jsonData = await response.json();
                    
                    // Show success message
                    showFormMessage(form, successMessage, 'success');
                    
                    // Call the success callback if provided
                    if (onSuccess && typeof onSuccess === 'function') {
                        onSuccess(jsonData);
                    }
                    
                    // Reset the form
                    form.reset();
                } else {
                    // Not JSON, likely HTML
                    console.log('Response is not JSON. Assuming success and redirecting.');
                    
                    // Show success message
                    showFormMessage(form, successMessage, 'success');
                    
                    // Get text and check if it contains a redirect URL
                    const text = await response.text();
                    
                    // Check if this looks like an HTML page with a redirect
                    if (text.includes('<html') && text.includes('redirect')) {
                        // Try to extract the URL (simple method)
                        const urlMatch = text.match(/window\.location\.href\s*=\s*['"]([^'"]+)['"]/);
                        if (urlMatch && urlMatch[1]) {
                            window.location.href = urlMatch[1];
                            return false;
                        }
                    }
                    
                    // If we couldn't extract a redirect URL, reload the current page
                    window.location.reload();
                    return false;
                }
            } else {
                // Try to parse error response
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    showFormMessage(form, errorData.error || 'Error submitting form', 'error');
                } else {
                    showFormMessage(form, `Error submitting form (${response.status})`, 'error');
                }
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            
            // If the error is due to being offline
            if (!navigator.onLine) {
                console.log('OfflineFormManager: Network error, saving form submission for later:', formId);
                
                try {
                    await offlineFormManager.saveRequest(endpoint, method, data, formId);
                    
                    // Show offline message
                    showFormMessage(form, offlineMessage, 'info');
                    
                    // Call the offline callback if provided
                    if (onOffline && typeof onOffline === 'function') {
                        onOffline(data);
                    }
                } catch (dbError) {
                    console.error('OfflineFormManager: Error saving form submission:', dbError);
                    showFormMessage(form, 'Error saving form data for offline submission', 'error');
                }
            } else {
                showFormMessage(form, 'Network error when submitting form', 'error');
            }
        }
        
        return false;
    };
}

/**
 * Show a message in a form
 * @param {HTMLFormElement} form - The form element
 * @param {string} message - Message to display
 * @param {string} type - Message type: 'success', 'error', 'info'
 */
function showFormMessage(form, message, type = 'info') {
    // Find existing message container or create one
    let messageContainer = form.querySelector('.form-message');
    
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.className = 'form-message';
        form.appendChild(messageContainer);
    }
    
    // Set message content and type
    messageContainer.textContent = message;
    messageContainer.className = `form-message form-message-${type}`;
    
    // Add styles if not already added
    if (!document.getElementById('form-message-styles')) {
        const style = document.createElement('style');
        style.id = 'form-message-styles';
        style.textContent = `
            .form-message {
                padding: 12px 16px;
                margin: 16px 0;
                border-radius: 4px;
                font-weight: 500;
            }
            .form-message-success {
                background-color: #e8f5e9;
                color: #2e7d32;
                border-left: 4px solid #2e7d32;
            }
            .form-message-error {
                background-color: #fdecea;
                color: #d32f2f;
                border-left: 4px solid #d32f2f;
            }
            .form-message-info {
                background-color: #e3f2fd;
                color: #0277bd;
                border-left: 4px solid #0277bd;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Show the message
    messageContainer.style.display = 'block';
    
    // Automatically hide success/info messages after 5 seconds
    if (type !== 'error') {
        setTimeout(() => {
            if (messageContainer) {
                messageContainer.style.display = 'none';
            }
        }, 5000);
    }
} 