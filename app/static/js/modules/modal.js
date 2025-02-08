// Modal Module

export function initializeModals() {
    // Initialize all modals on the page
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        // Initialize close buttons
        const closeButtons = modal.querySelectorAll('.modal-close, [data-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                closeModal(modal);
            });
        });

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
}

export function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

export function closeModal(modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
}

// Export additional modal-related functions
export { initializeModals as default }; 