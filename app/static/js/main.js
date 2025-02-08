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

// Initialize all modules when the DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Content Loaded');
    
    try {
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
    }
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // You could send this to your error tracking service
}); 