// FoodBridge JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('fade-in');
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Form validation improvements
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                
                // Re-enable button after 10 seconds as fallback
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Submit';
                }, 10000);
            }
        });
    });
    
    // Store original button text for form submissions
    const submitBtns = document.querySelectorAll('button[type="submit"]');
    submitBtns.forEach(function(btn) {
        btn.setAttribute('data-original-text', btn.innerHTML);
    });
    
    // Donation form enhancements
    const availableFromInput = document.getElementById('available_from');
    const availableUntilInput = document.getElementById('available_until');
    
    if (availableFromInput && availableUntilInput) {
        // Update minimum "until" time when "from" time changes
        availableFromInput.addEventListener('change', function() {
            const fromDate = new Date(this.value);
            const minUntilDate = new Date(fromDate.getTime() + 30 * 60 * 1000); // 30 minutes later
            availableUntilInput.min = minUntilDate.toISOString().slice(0, 16);
            
            // If until date is before the new minimum, update it
            if (availableUntilInput.value && new Date(availableUntilInput.value) < minUntilDate) {
                availableUntilInput.value = minUntilDate.toISOString().slice(0, 16);
            }
        });
    }
    
    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 6) {
                value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
            } else if (value.length >= 3) {
                value = value.replace(/(\d{3})(\d{0,3})/, '($1) $2');
            }
            e.target.value = value;
        });
    });
    
    // Confirm dialogs for important actions
    const confirmBtns = document.querySelectorAll('[data-confirm]');
    confirmBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // Real-time character counter for textareas
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(function(textarea) {
        const maxLength = textarea.getAttribute('maxlength');
        const counter = document.createElement('small');
        counter.className = 'form-text text-muted';
        counter.style.textAlign = 'right';
        counter.style.display = 'block';
        
        const updateCounter = function() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} characters remaining`;
            if (remaining < 10) {
                counter.className = 'form-text text-warning';
            } else {
                counter.className = 'form-text text-muted';
            }
        };
        
        textarea.parentNode.appendChild(counter);
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
    
    // Auto-refresh donation listings every 2 minutes
    if (window.location.pathname.includes('/charity/dashboard')) {
        setInterval(function() {
            // Only refresh if the page is visible and user hasn't scrolled recently
            if (!document.hidden && (Date.now() - lastScrollTime) > 60000) {
                location.reload();
            }
        }, 120000);
    }
    
    // Track last scroll time to prevent interrupting user interaction
    let lastScrollTime = Date.now();
    window.addEventListener('scroll', function() {
        lastScrollTime = Date.now();
    });
    
    // Clipboard functionality for contact information
    const copyBtns = document.querySelectorAll('.copy-btn');
    copyBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const text = this.getAttribute('data-copy');
            navigator.clipboard.writeText(text).then(function() {
                // Show success feedback
                const originalText = btn.innerHTML;
                btn.innerHTML = '✓ Copied!';
                setTimeout(function() {
                    btn.innerHTML = originalText;
                }, 2000);
            });
        });
    });
    
    // Enhanced accessibility
    const navToggle = document.querySelector('.navbar-toggler');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !expanded);
        });
    }
    
    // Keyboard navigation improvements
    document.addEventListener('keydown', function(e) {
        // ESC key closes modals and dropdowns
        if (e.key === 'Escape') {
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(function(dropdown) {
                const toggle = dropdown.previousElementSibling;
                if (toggle) {
                    const bsDropdown = bootstrap.Dropdown.getInstance(toggle);
                    if (bsDropdown) {
                        bsDropdown.hide();
                    }
                }
            });
        }
    });
});

// Utility functions
function showToast(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

function formatPhoneNumber(phone) {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Service Worker registration for potential PWA features
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment when service worker is implemented
        // navigator.serviceWorker.register('/static/js/sw.js');
    });
}