// Navigation Module
export class Navigation {
    constructor() {
        this.mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        this.navLinks = document.querySelector('.nav-links');
        this.init();
    }

    init() {
        if (this.mobileMenuToggle && this.navLinks) {
            this.setupMobileMenu();
            this.setupClickOutside();
            this.setupResizeHandler();
            this.setupKeyboardNavigation();
        }
    }

    setupMobileMenu() {
        this.mobileMenuToggle.addEventListener('click', () => {
            const isExpanded = this.mobileMenuToggle.getAttribute('aria-expanded') === 'true';
            this.mobileMenuToggle.setAttribute('aria-expanded', !isExpanded);
            this.navLinks.classList.toggle('active');
        });
    }

    setupClickOutside() {
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.nav-links') && !event.target.closest('.mobile-menu-toggle')) {
                this.navLinks.classList.remove('active');
                this.mobileMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    setupResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (window.innerWidth > 768) {
                    this.navLinks.classList.remove('active');
                    this.mobileMenuToggle.setAttribute('aria-expanded', 'false');
                }
            }, 100);
        });
    }

    setupKeyboardNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    link.click();
                }
            });
        });

        // Add arrow key navigation for dropdown menus
        document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('keydown', (e) => {
                const menu = toggle.nextElementSibling;
                if (!menu) return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    menu.querySelector('.dropdown-item')?.focus();
                }
            });
        });

        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            const items = menu.querySelectorAll('.dropdown-item');
            items.forEach((item, index) => {
                item.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        items[index + 1]?.focus();
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        if (index === 0) {
                            menu.previousElementSibling?.focus();
                        } else {
                            items[index - 1]?.focus();
                        }
                    } else if (e.key === 'Escape') {
                        e.preventDefault();
                        menu.previousElementSibling?.focus();
                    }
                });
            });
        });
    }
}

// Initialize navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new Navigation();
}); 