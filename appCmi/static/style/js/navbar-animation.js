/**
 * Mobile Responsive Navbar JavaScript
 * Handles mobile menu, dropdowns, and responsive interactions
 */

// Global namespace for navbar functionality
const NavbarController = {
    // State management
    state: {
        mobileMenuOpen: false,
        activeDropdowns: new Set(),
        isInitialized: false
    },
    
    // Element references (cached for performance)
    elements: {},
    
    // Configuration
    config: {
        mobileBreakpoint: 768,
        resizeDebounceDelay: 250,
        scrollThrottleDelay: 16,
        hoverDelay: 150,
        animationDuration: 600
    },

    // Initialize all navbar functionality
    init() {
        if (this.state.isInitialized) {
            console.warn('Navbar already initialized');
            return;
        }

        this.cacheElements();
        this.initMobileMenu();
        this.initMobileDropdowns();
        this.initDesktopHovers();
        this.initResponsiveHandlers();
        this.initAccessibility();
        this.initSmoothScrolling();
        this.initUserFeedback();
        this.initPerformanceOptimizations();
        this.initDebugHelpers();
        
        this.state.isInitialized = true;
        console.log('🚀 Mobile Responsive Navbar initialized successfully!');
    },

    /**
     * Cache DOM elements for better performance
     */
    cacheElements() {
        this.elements = {
            hamburger: document.querySelector('.hamburger'),
            mobileMenu: document.querySelector('.mobile-menu'),
            navbar: document.querySelector('.navbar'),
            mobileDropdowns: document.querySelectorAll('.mobile-dropdown'),
            desktopDropdowns: document.querySelectorAll('.desktop-menu .dropdown'),
            anchorLinks: document.querySelectorAll('a[href^="#"]'),
            externalLinks: document.querySelectorAll('a[href]:not([href^="#"]):not([href^="/"])'),
            interactiveElements: document.querySelectorAll('.hamburger, .mobile-dropdown-toggle, .navbar-center a')
        };
    },

    /**
     * Initialize mobile menu toggle functionality
     */
    initMobileMenu() {
        const { hamburger, mobileMenu } = this.elements;

        if (!hamburger || !mobileMenu) {
            console.warn('Mobile menu elements not found');
            return;
        }

        hamburger.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleMobileMenu();
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (event) => {
            if (this.state.mobileMenuOpen) {
                const isClickInsideMenu = mobileMenu.contains(event.target);
                const isClickOnHamburger = hamburger.contains(event.target);
                
                if (!isClickInsideMenu && !isClickOnHamburger) {
                    this.closeMobileMenu();
                }
            }
        });
    },

    /**
     * Toggle mobile menu state
     */
    toggleMobileMenu() {
        if (this.state.mobileMenuOpen) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    },

    /**
     * Open mobile menu with animations
     */
    openMobileMenu() {
        const { hamburger, mobileMenu } = this.elements;
        
        mobileMenu.classList.add('visible');
        hamburger.classList.add('open');
        hamburger.setAttribute('aria-expanded', 'true');
        this.state.mobileMenuOpen = true;

        // Update hamburger icon
        const icon = hamburger.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-times');
        }

        // Prevent body scroll on mobile
        if (window.innerWidth <= this.config.mobileBreakpoint) {
            document.body.style.overflow = 'hidden';
        }
    },

    /**
     * Close mobile menu with animations
     */
    closeMobileMenu() {
        const { hamburger, mobileMenu } = this.elements;
        
        mobileMenu.classList.remove('visible');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
        this.state.mobileMenuOpen = false;

        // Reset hamburger icon
        const icon = hamburger.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }

        // Restore body scroll
        document.body.style.overflow = '';

        // Close all mobile dropdowns
        this.closeMobileDropdowns();
    },

    /**
     * Initialize mobile dropdown functionality
     */
    initMobileDropdowns() {
        this.elements.mobileDropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.mobile-dropdown-toggle');
            const content = dropdown.querySelector('.mobile-dropdown-content');
            
            if (!toggle || !content) return;

            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const isOpen = dropdown.classList.contains('open');
                
                // Close other dropdowns
                this.elements.mobileDropdowns.forEach(otherDropdown => {
                    if (otherDropdown !== dropdown) {
                        this.closeDropdown(otherDropdown);
                    }
                });
                
                // Toggle current dropdown
                if (isOpen) {
                    this.closeDropdown(dropdown);
                } else {
                    this.openDropdown(dropdown);
                }
            });
        });
    },

    /**
     * Open a mobile dropdown
     */
    openDropdown(dropdown) {
        const toggle = dropdown.querySelector('.mobile-dropdown-toggle');
        const content = dropdown.querySelector('.mobile-dropdown-content');
        
        dropdown.classList.add('open');
        content.classList.add('open');
        toggle.setAttribute('aria-expanded', 'true');
        this.state.activeDropdowns.add(dropdown);
    },

    /**
     * Close a mobile dropdown
     */
    closeDropdown(dropdown) {
        const toggle = dropdown.querySelector('.mobile-dropdown-toggle');
        const content = dropdown.querySelector('.mobile-dropdown-content');
        
        dropdown.classList.remove('open');
        content.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        this.state.activeDropdowns.delete(dropdown);
    },

    /**
     * Close all mobile dropdowns
     */
    closeMobileDropdowns() {
        this.elements.mobileDropdowns.forEach(dropdown => {
            this.closeDropdown(dropdown);
        });
        this.state.activeDropdowns.clear();
    },

    /**
     * Initialize desktop dropdown hover effects
     */
    initDesktopHovers() {
        this.elements.desktopDropdowns.forEach(dropdown => {
            let hoverTimeout;
            const menu = dropdown.querySelector('.dropdown-menu');
            const toggle = dropdown.querySelector('a[aria-haspopup="true"]');
            
            if (!menu || !toggle) return;

            dropdown.addEventListener('mouseenter', () => {
                clearTimeout(hoverTimeout);
                this.showDropdownMenu(menu, toggle);
            });
            
            dropdown.addEventListener('mouseleave', () => {
                hoverTimeout = setTimeout(() => {
                    this.hideDropdownMenu(menu, toggle);
                }, this.config.hoverDelay);
            });

            // Handle keyboard navigation
            toggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const isVisible = menu.style.opacity === '1';
                    
                    if (isVisible) {
                        this.hideDropdownMenu(menu, toggle);
                    } else {
                        this.showDropdownMenu(menu, toggle);
                    }
                }
            });
        });
    },

    /**
     * Show dropdown menu with animation
     */
    showDropdownMenu(menu, toggle) {
        menu.style.opacity = '1';
        menu.style.visibility = 'visible';
        menu.style.transform = 'translateY(0)';
        toggle.setAttribute('aria-expanded', 'true');
    },

    /**
     * Hide dropdown menu with animation
     */
    hideDropdownMenu(menu, toggle) {
        menu.style.opacity = '0';
        menu.style.visibility = 'hidden';
        menu.style.transform = 'translateY(-10px)';
        toggle.setAttribute('aria-expanded', 'false');
    },

    /**
     * Initialize responsive handlers
     */
    initResponsiveHandlers() {
        let resizeTimer;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                this.handleResize();
            }, this.config.resizeDebounceDelay);
        });
    },

    /**
     * Handle window resize events
     */
    handleResize() {
        const { mobileMenu, hamburger } = this.elements;
        
        // Close mobile menu on desktop resize
        if (window.innerWidth > this.config.mobileBreakpoint) {
            if (this.state.mobileMenuOpen) {
                this.closeMobileMenu();
            }
            
            // Reset hamburger state
            if (hamburger) {
                hamburger.classList.remove('open');
                hamburger.setAttribute('aria-expanded', 'false');
                
                const icon = hamburger.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
            
            // Close mobile dropdowns
            this.closeMobileDropdowns();
            
            // Restore body scroll
            document.body.style.overflow = '';
        }
        
        // Close desktop dropdowns on mobile resize
        if (window.innerWidth <= this.config.mobileBreakpoint) {
            const desktopDropdowns = document.querySelectorAll('.desktop-menu .dropdown-menu');
            desktopDropdowns.forEach(menu => {
                menu.style.opacity = '0';
                menu.style.visibility = 'hidden';
                menu.style.transform = 'translateY(-10px)';
            });
        }
    },

    /**
     * Initialize accessibility features
     */
    initAccessibility() {
        // Keyboard navigation (ESC key)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleEscapeKey();
            }
            
            // Tab navigation improvements
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });

        // Add ARIA labels and roles where needed
        this.enhanceAccessibility();
    },

    /**
     * Handle escape key press
     */
    handleEscapeKey() {
        const { hamburger } = this.elements;
        
        // Close mobile menu
        if (this.state.mobileMenuOpen) {
            this.closeMobileMenu();
            
            // Focus back to hamburger
            if (hamburger) {
                hamburger.focus();
            }
        }
        
        // Close mobile dropdowns
        this.closeMobileDropdowns();
        
        // Close desktop dropdowns
        const desktopDropdowns = document.querySelectorAll('.desktop-menu .dropdown-menu');
        desktopDropdowns.forEach(menu => {
            const toggle = menu.parentElement.querySelector('a[aria-haspopup="true"]');
            menu.style.opacity = '0';
            menu.style.visibility = 'hidden';
            menu.style.transform = 'translateY(-10px)';
            if (toggle) {
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
    },

    /**
     * Handle tab navigation for better accessibility
     */
    handleTabNavigation(e) {
        const { mobileMenu } = this.elements;
        
        // Trap focus within mobile menu when open
        if (this.state.mobileMenuOpen) {
            const focusableElements = mobileMenu.querySelectorAll(
                'a, button, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
    },

    /**
     * Enhance accessibility attributes
     */
    enhanceAccessibility() {
        const { hamburger } = this.elements;
        
        if (hamburger && !hamburger.getAttribute('aria-label')) {
            hamburger.setAttribute('aria-label', 'Toggle mobile menu');
        }

        // Enhance dropdown accessibility
        const dropdownToggles = document.querySelectorAll('[aria-haspopup="true"]');
        dropdownToggles.forEach(toggle => {
            if (!toggle.getAttribute('role')) {
                toggle.setAttribute('role', 'button');
            }
        });
    },

    /**
     * Initialize smooth scrolling for anchor links
     */
    initSmoothScrolling() {
        this.elements.anchorLinks.forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                const targetId = anchor.getAttribute('href');
                
                // Skip if it's just a hash or placeholder
                if (targetId === '#' || targetId === '#!') {
                    e.preventDefault();
                    return;
                }
                
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    
                    // Calculate offset accounting for navbar height
                    const navbarHeight = this.elements.navbar?.offsetHeight || 70;
                    const offsetTop = targetElement.offsetTop - navbarHeight - 20;
                    
                    window.scrollTo({
                        top: Math.max(0, offsetTop),
                        behavior: 'smooth'
                    });
                    
                    // Close mobile menu if open
                    if (this.state.mobileMenuOpen) {
                        this.closeMobileMenu();
                    }
                    
                    // Update focus for accessibility
                    setTimeout(() => {
                        targetElement.focus({ preventScroll: true });
                    }, 500);
                }
            });
        });
    },

    /**
     * Add loading states and user feedback
     */
    initUserFeedback() {
        // Add subtle loading indication for external links
        this.elements.externalLinks.forEach(link => {
            link.addEventListener('click', function() {
                this.style.opacity = '0.7';
                this.style.transform = 'scale(0.98)';
                
                setTimeout(() => {
                    this.style.opacity = '';
                    this.style.transform = '';
                }, 200);
            });
        });

        // Add ripple effect to interactive elements
        this.elements.interactiveElements.forEach(element => {
            element.addEventListener('click', (e) => {
                this.createRippleEffect(element, e);
            });
        });

        // Add ripple CSS if not exists
        this.addRippleStyles();
    },

    /**
     * Create ripple effect on click
     */
    createRippleEffect(element, event) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        
        // Calculate position
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        // Style the ripple
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        ripple.className = 'navbar-ripple';
        
        // Remove existing ripples
        const existingRipple = element.querySelector('.navbar-ripple');
        if (existingRipple) {
            existingRipple.remove();
        }
        
        // Add new ripple
        element.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(() => {
            ripple.remove();
        }, this.config.animationDuration);
    },

    /**
     * Add ripple effect styles
     */
    addRippleStyles() {
        if (!document.querySelector('#navbar-ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'navbar-ripple-styles';
            style.textContent = `
                .navbar-ripple {
                    position: absolute;
                    border-radius: 50%;
                    background-color: rgba(255, 255, 255, 0.4);
                    transform: scale(0);
                    animation: navbar-ripple-animation 0.6s linear;
                    pointer-events: none;
                    z-index: 0;
                }
                
                @keyframes navbar-ripple-animation {
                    to {
                        transform: scale(2.5);
                        opacity: 0;
                    }
                }
                
                .hamburger,
                .mobile-dropdown-toggle,
                .navbar-center a {
                    position: relative;
                    overflow: hidden;
                }
            `;
            document.head.appendChild(style);
        }
    },

    /**
     * Initialize performance optimizations
     */
    initPerformanceOptimizations() {
        // Throttle scroll events for better performance
        this.initScrollHandler();
        
        // Optimize resize events with ResizeObserver
        this.initResizeObserver();
    },

    /**
     * Initialize optimized scroll handler
     */
    initScrollHandler() {
        let scrollTimer;
        window.addEventListener('scroll', () => {
            if (scrollTimer) return;
            
            scrollTimer = setTimeout(() => {
                this.handleScroll();
                scrollTimer = null;
            }, this.config.scrollThrottleDelay);
        });
    },

    /**
     * Handle scroll events efficiently
     */
    handleScroll() {
        const { navbar } = this.elements;
        if (!navbar) return;

        // Add shadow on scroll
        if (window.scrollY > 10) {
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
        } else {
            navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
    },

    /**
     * Initialize ResizeObserver for better performance
     */
    initResizeObserver() {
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(entries => {
                for (let entry of entries) {
                    if (entry.target === document.body) {
                        // Use the bound handleResize method
                        this.handleResize();
                    }
                }
            });
            
            resizeObserver.observe(document.body);
        }
    },

    /**
     * Debug and development helpers
     */
    initDebugHelpers() {
        if (this.isDevelopment()) {
            console.log('🔧 Navbar Debug Mode Enabled');
            
            const logBreakpoint = () => {
                const width = window.innerWidth;
                let breakpoint = 'XL';
                
                if (width <= 360) breakpoint = 'XS';
                else if (width <= 480) breakpoint = 'SM';
                else if (width <= 768) breakpoint = 'MD';
                else if (width <= 1024) breakpoint = 'LG';
                
                console.log(`📱 Current breakpoint: ${breakpoint} (${width}px)`);
            };
            
            window.addEventListener('resize', logBreakpoint);
            logBreakpoint();

            // Expose controller to global scope for debugging
            window.NavbarController = this;
        }
    },

    /**
     * Check if running in development environment
     */
    isDevelopment() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname.includes('dev') ||
               window.location.search.includes('debug=true');
    },

    /**
     * Public API methods
     */
    getState() {
        return { ...this.state };
    },

    getConfig() {
        return { ...this.config };
    },

    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    NavbarController.init();
});

// Expose public API
window.NavbarUtils = {
    openMobileMenu: () => NavbarController.openMobileMenu(),
    closeMobileMenu: () => NavbarController.closeMobileMenu(),
    closeMobileDropdowns: () => NavbarController.closeMobileDropdowns(),
    getState: () => NavbarController.getState(),
    getConfig: () => NavbarController.getConfig(),
    updateConfig: (config) => NavbarController.updateConfig(config)
};

// Legacy compatibility
window.openMobileMenu = () => NavbarController.openMobileMenu();
window.closeMobileMenu = () => NavbarController.closeMobileMenu();
window.closeMobileDropdowns = () => NavbarController.closeMobileDropdowns();