// Profile page functionality
document.addEventListener('DOMContentLoaded', () => {
    // Initialize status filter
    const statusFilter = document.querySelector('.status-filter select');
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            e.target.closest('form').submit();
        });
    }

    // Initialize search functionality
    const searchForm = document.querySelector('.filters-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchForm.submit();
            }, 500);
        });
    }

    // Handle shipment card clicks
    const shipmentCards = document.querySelectorAll('.shipment-card');
    shipmentCards.forEach(card => {
        const viewButton = card.querySelector('.btn-outline');
        if (viewButton) {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.btn')) {
                    viewButton.click();
                }
            });
        }
    });

    // Initialize status badge tooltips
    const statusBadges = document.querySelectorAll('.status-badge');
    statusBadges.forEach(badge => {
        const status = badge.textContent.trim().toLowerCase();
        let tooltip = '';

        switch (status) {
            case 'pending':
                tooltip = 'Shipment is awaiting processing';
                break;
            case 'processing':
                tooltip = 'Shipment is being processed';
                break;
            case 'in_transit':
                tooltip = 'Shipment is on its way';
                break;
            case 'delivered':
                tooltip = 'Shipment has been delivered';
                break;
            case 'cancelled':
                tooltip = 'Shipment has been cancelled';
                break;
        }

        if (tooltip) {
            badge.setAttribute('title', tooltip);
            badge.setAttribute('data-bs-toggle', 'tooltip');
            badge.setAttribute('data-bs-placement', 'top');
        }
    });

    // Initialize Bootstrap tooltips
    if (typeof bootstrap !== 'undefined') {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }

    // Handle mobile responsiveness
    const handleResize = () => {
        const container = document.querySelector('.shipments-container');
        if (container) {
            const width = window.innerWidth;
            if (width <= 768) {
                // Mobile view adjustments
                const cards = container.querySelectorAll('.shipment-card');
                cards.forEach(card => {
                    const meta = card.querySelector('.shipment-meta');
                    if (meta) {
                        meta.style.flexDirection = 'column';
                        meta.style.gap = '0.5rem';
                    }
                });
            } else {
                // Desktop view adjustments
                const cards = container.querySelectorAll('.shipment-card');
                cards.forEach(card => {
                    const meta = card.querySelector('.shipment-meta');
                    if (meta) {
                        meta.style.flexDirection = 'row';
                        meta.style.gap = '1.5rem';
                    }
                });
            }
        }
    };

    // Initial call and event listener for resize
    handleResize();
    window.addEventListener('resize', handleResize);

    // Handle status updates via AJAX
    const setupStatusUpdates = () => {
        const statusForms = document.querySelectorAll('.status-update-form');
        statusForms.forEach(form => {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const shipmentId = form.dataset.shipmentId;

                try {
                    // Get CSRF token
                    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
                    
                    const response = await fetch(`/profile/api/shipments/${shipmentId}/status`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-TOKEN': csrfToken
                        },
                        body: JSON.stringify({
                            status: formData.get('status')
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // Update UI with new status
                        const card = form.closest('.shipment-card');
                        if (card) {
                            const badge = card.querySelector('.status-badge');
                            if (badge) {
                                badge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                                badge.className = `status-badge ${data.status}`;
                            }
                        }
                    } else {
                        throw new Error('Failed to update status');
                    }
                } catch (error) {
                    console.error('Error updating status:', error);
                    alert('Failed to update shipment status. Please try again.');
                }
            });
        });
    };

    setupStatusUpdates();
}); 