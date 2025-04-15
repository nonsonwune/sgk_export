// Item entry counter
let itemCounter = 1;

// Function to add new item entry
function addItemEntry() {
    const container = document.getElementById('items-container');
    const newEntry = document.createElement('div');
    newEntry.className = 'item-entry';
    
    newEntry.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label for="description_${itemCounter}" class="form-label required">Description</label>
                <input type="text" id="description_${itemCounter}" name="description[]" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="value_${itemCounter}" class="form-label required">Value</label>
                <input type="number" id="value_${itemCounter}" name="value[]" class="form-control" step="0.01" required>
            </div>
            <div class="form-group">
                <label for="quantity_${itemCounter}" class="form-label required">Quantity</label>
                <input type="number" id="quantity_${itemCounter}" name="quantity[]" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="weight_${itemCounter}" class="form-label required">Weight (kg)</label>
                <input type="number" id="weight_${itemCounter}" name="weight[]" class="form-control" step="0.1" required>
            </div>
            <div class="form-group">
                <label for="item_image_${itemCounter}" class="form-label">Item Image</label>
                <input type="file" id="item_image_${itemCounter}" name="item_image[]" class="form-control" accept="image/*">
            </div>
        </div>
        <button type="button" class="btn btn-danger remove-item-btn" onclick="removeItemEntry(this)">
            <i class="fas fa-trash"></i> Remove Item
        </button>
    `;
    
    container.appendChild(newEntry);
    itemCounter++;
}

// Function to remove item entry
function removeItemEntry(button) {
    button.parentElement.remove();
}

// Main JavaScript file
console.log('Loading main.js');

// Import modules
import { initializeModals } from './modules/modal.js';
import { initializeFormValidation } from './modules/validation.js';
import { initializePrint } from './modules/print.js';

// Initialize all modules when the DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Content Loaded');
    
    try {
        // Initialize print functionality if on print template page
        if (document.querySelector('.print-content')) {
            console.log('Initializing print functionality');
            initializePrint();
        }

        // Debug style application
        console.log('Verifying critical styles...');
        const formCardHeaders = document.querySelectorAll('.form-card-header');
        console.log(`Found ${formCardHeaders.length} form card headers`);
        
        const pricingGrid = document.querySelector('.pricing-grid');
        if (pricingGrid) {
            console.log('Pricing grid found');
            const computedStyle = window.getComputedStyle(pricingGrid);
            console.log('Pricing grid display:', computedStyle.display);
            console.log('Pricing grid template columns:', computedStyle.gridTemplateColumns);
        }
        
        const totalSection = document.querySelector('.total-section');
        if (totalSection) {
            console.log('Total section found');
            console.log('Total section border:', window.getComputedStyle(totalSection).borderTopWidth);
        }

        // Initialize Bootstrap components
        console.log('Initializing Bootstrap components');
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize custom modules
        console.log('Initializing custom modules');
        
        // Initialize modals if the function exists
        if (typeof initializeModals === 'function') {
            console.log('Initializing modals');
            initializeModals();
        } else {
            console.warn('Modal initialization skipped - function not available');
        }

        // Initialize form validation if the function exists
        if (typeof initializeFormValidation === 'function') {
            console.log('Initializing form validation');
            initializeFormValidation();
        } else {
            console.warn('Form validation initialization skipped - function not available');
        }

        // Initialize alerts
        console.log('Initializing alerts');
        initializeAlerts();

        // Initialize pricing calculations only if we're on a page with pricing elements
        console.log('Checking for pricing elements');
        if (document.getElementById('subtotal') && 
            document.getElementById('vat') && 
            document.getElementById('total')) {
            console.log('Pricing elements found, initializing calculations');
            initializePricingCalculations();
        } else {
            console.log('No pricing elements found, skipping calculations');
        }

    } catch (error) {
        console.error('Error during initialization:', error);
    }
});

// Separate function for pricing calculations
function initializePricingCalculations() {
    try {
        // Get all pricing input fields
        const pricingInputs = document.querySelectorAll([
            '#freight',
            '#additional',
            '#pickup',
            '#handling',
            '#crating',
            '#insurance'
        ].join(','));

        console.log(`Found ${pricingInputs.length} pricing input fields`);

        // Function to calculate totals
        function calculateTotals() {
            try {
                let subtotal = 0;
                
                // Calculate subtotal
                pricingInputs.forEach(input => {
                    const value = parseFloat(input.value || 0);
                    console.log(`Adding value from ${input.id}: ${value}`);
                    subtotal += value;
                });

                // Calculate VAT and total
                const vat = subtotal * 0.07;
                const total = subtotal + vat;

                // Update the display
                const subtotalElement = document.getElementById('subtotal');
                const vatElement = document.getElementById('vat');
                const totalElement = document.getElementById('total');

                if (subtotalElement && vatElement && totalElement) {
                    subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
                    vatElement.textContent = `$${vat.toFixed(2)}`;
                    totalElement.textContent = `$${total.toFixed(2)}`;
                    console.log(`Updated totals - Subtotal: ${subtotal}, VAT: ${vat}, Total: ${total}`);
                }
            } catch (error) {
                console.error('Error calculating totals:', error);
            }
        }

        // Add event listeners to pricing inputs
        pricingInputs.forEach(input => {
            input.addEventListener('input', calculateTotals);
        });

        // Initial calculation
        calculateTotals();
    } catch (error) {
        console.error('Error initializing pricing calculations:', error);
    }
}

// Alert auto-hide functionality
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    console.log(`Found ${alerts.length} alerts to initialize`);
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

// Global AJAX setup
$.ajaxSetup({
    headers: {
        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.content
    },
    beforeSend: function(xhr, settings) {
        // Only add the CSRF token for POST, PUT, DELETE requests
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRF-TOKEN", document.querySelector('meta[name="csrf-token"]')?.content);
        }
    }
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // You could send this to your error tracking service
});

// PWA Functionality
let deferredPrompt;
const pwaVersion = '1.0.0'; // Update this when releasing a new version

// Handle PWA install prompt
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show install promotion after user has been on the site for 30 seconds
    setTimeout(() => {
        if (deferredPrompt && !localStorage.getItem('pwa-install-dismissed')) {
            showPWAInstallPrompt();
        }
    }, 30000);
});

// Create and show PWA install banner
function showPWAInstallPrompt() {
    // Create banner element
    const banner = document.createElement('div');
    banner.className = 'pwa-install-banner';
    banner.innerHTML = `
        <div class="pwa-banner-content">
            <img src="/static/images/icons/icon-192x192.png" alt="SGK Export App Icon" class="pwa-banner-icon">
            <div class="pwa-banner-text">
                <p>Install SGK Export for offline access</p>
                <p class="pwa-banner-subtitle">Access shipment information even without internet</p>
            </div>
        </div>
        <div class="pwa-banner-actions">
            <button id="pwa-install-btn" class="btn btn-primary">Install</button>
            <button id="pwa-dismiss-btn" class="btn btn-link">Not now</button>
        </div>
    `;
    
    // Add banner styles
    const style = document.createElement('style');
    style.textContent = `
        .pwa-install-banner {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 12px 16px;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            animation: slide-up 0.3s ease-out;
        }
        @keyframes slide-up {
            from { transform: translateY(100%); }
            to { transform: translateY(0); }
        }
        .pwa-banner-content {
            display: flex;
            align-items: center;
        }
        .pwa-banner-icon {
            width: 48px;
            height: 48px;
            margin-right: 16px;
        }
        .pwa-banner-text {
            flex: 1;
        }
        .pwa-banner-text p {
            margin: 0;
        }
        .pwa-banner-subtitle {
            font-size: 0.8rem;
            color: #666;
        }
        .pwa-banner-actions {
            display: flex;
            gap: 8px;
        }
    `;
    
    // Add to DOM
    document.head.appendChild(style);
    document.body.appendChild(banner);
    
    // Add event listeners
    document.getElementById('pwa-install-btn').addEventListener('click', async () => {
        // Hide the banner
        banner.remove();
        
        // Show the install prompt
        if (deferredPrompt) {
            deferredPrompt.prompt();
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User ${outcome} the A2HS prompt`);
            
            // Clear the saved prompt since it can't be used again
            deferredPrompt = null;
        }
    });
    
    document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
        banner.remove();
        // Save preference in localStorage to not show again for a week
        const now = new Date();
        const expiryTime = now.getTime() + (7 * 24 * 60 * 60 * 1000); // 7 days
        localStorage.setItem('pwa-install-dismissed', expiryTime.toString());
    });
}

// Check service worker version
function checkServiceWorkerVersion() {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
            type: 'CHECK_VERSION',
            version: pwaVersion
        });
    }
}

// Listen for messages from service worker
navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'VERSION_STATUS' && event.data.needsUpdate) {
        showUpdateNotification();
    }
});

// Show update notification
function showUpdateNotification() {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
        <div class="update-notification-content">
            <i class="fas fa-sync-alt"></i>
            <span>A new version is available. Refresh to update.</span>
        </div>
        <button id="update-now-btn" class="btn btn-sm btn-primary">Update Now</button>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .update-notification {
            position: fixed;
            top: 16px;
            right: 16px;
            background: white;
            padding: 12px 16px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            animation: fade-in 0.3s ease-out;
        }
        @keyframes fade-in {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .update-notification-content {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .update-notification i {
            color: #4169E1;
        }
    `;
    
    // Add to DOM
    document.head.appendChild(style);
    document.body.appendChild(notification);
    
    // Add event listener
    document.getElementById('update-now-btn').addEventListener('click', () => {
        window.location.reload();
    });
}

// Call these functions when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check for service worker updates
    setTimeout(checkServiceWorkerVersion, 5000);
}); 