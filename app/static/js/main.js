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
                <label for="description_${itemCounter}">Description</label>
                <input type="text" id="description_${itemCounter}" name="description[]" required>
            </div>
            <div class="form-group">
                <label for="value_${itemCounter}">Value</label>
                <input type="number" id="value_${itemCounter}" name="value[]" required>
            </div>
            <div class="form-group">
                <label for="quantity_${itemCounter}">Quantity</label>
                <input type="number" id="quantity_${itemCounter}" name="quantity[]" required>
            </div>
            <div class="form-group">
                <label for="weight_${itemCounter}">Weight (kg)</label>
                <input type="number" id="weight_${itemCounter}" name="weight[]" step="0.1" required>
            </div>
            <div class="form-group">
                <label for="item_image_${itemCounter}">Item Image</label>
                <input type="file" id="item_image_${itemCounter}" name="item_image[]" accept="image/*">
            </div>
        </div>
        <button type="button" class="remove-item-btn" onclick="removeItemEntry(this)">Remove Item</button>
    `;
    
    container.appendChild(newEntry);
    itemCounter++;
}

// Function to remove item entry
function removeItemEntry(button) {
    button.parentElement.remove();
}

document.addEventListener('DOMContentLoaded', function() {
    // Get all pricing input fields
    const pricingInputs = document.querySelectorAll([
        '#freight',
        '#additional',
        '#pickup',
        '#handling',
        '#crating',
        '#insurance'
    ].join(','));

    // Function to calculate totals
    function calculateTotals() {
        let subtotal = 0;
        
        // Calculate subtotal
        pricingInputs.forEach(input => {
            subtotal += parseFloat(input.value || 0);
        });

        // Calculate VAT and total
        const vat = subtotal * 0.07;
        const total = subtotal + vat;

        // Update the display
        document.getElementById('subtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('vat').textContent = `$${vat.toFixed(2)}`;
        document.getElementById('total').textContent = `$${total.toFixed(2)}`;
    }

    // Add event listeners to pricing inputs
    pricingInputs.forEach(input => {
        input.addEventListener('input', calculateTotals);
    });

    // Form validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Validate required fields
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            // Validate mobile numbers
            const mobileFields = [
                document.getElementById('sender_mobile'),
                document.getElementById('receiver_mobile')
            ];

            mobileFields.forEach(field => {
                if (field && !isValidMobile(field.value)) {
                    isValid = false;
                    field.classList.add('error');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields correctly.');
            }
        });
    }

    // Mobile number validation
    function isValidMobile(number) {
        return /^\d{10,}$/.test(number.replace(/\D/g, ''));
    }

    // Initialize calculations
    calculateTotals();
}); 