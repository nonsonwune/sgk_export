// Form Validation Module

export function initializeFormValidation() {
    // Initialize all forms with the 'needs-validation' class
    const forms = document.querySelectorAll('form.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });

        // Real-time validation for password confirmation
        const passwordField = form.querySelector('input[type="password"]');
        const confirmField = form.querySelector('input[name="confirm_password"]');
        
        if (passwordField && confirmField) {
            confirmField.addEventListener('input', () => {
                validatePasswordMatch(passwordField, confirmField);
            });
        }
    });
}

function validateForm(form) {
    let isValid = true;

    // Check required fields
    form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            showError(field, 'This field is required');
        } else {
            clearError(field);
        }
    });

    // Check email fields
    form.querySelectorAll('input[type="email"]').forEach(field => {
        if (field.value && !validateEmail(field.value)) {
            isValid = false;
            showError(field, 'Please enter a valid email address');
        }
    });

    // Check password fields
    const passwordField = form.querySelector('input[name="password"]');
    const confirmField = form.querySelector('input[name="confirm_password"]');
    
    if (passwordField && confirmField) {
        isValid = validatePasswordMatch(passwordField, confirmField) && isValid;
    }

    return isValid;
}

function validatePasswordMatch(passwordField, confirmField) {
    if (confirmField.value && passwordField.value !== confirmField.value) {
        showError(confirmField, 'Passwords do not match');
        return false;
    } else {
        clearError(confirmField);
        return true;
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email.toLowerCase());
}

function showError(field, message) {
    field.setCustomValidity(message);
    const feedback = field.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = message;
    }
}

function clearError(field) {
    field.setCustomValidity('');
}

export { validateForm, validateEmail }; 