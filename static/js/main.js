/* ============================================ */
/* RONGO HOMES - MAIN JAVASCRIPT                */
/* ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize all app functionality
 */
function initializeApp() {
    initializeAutoHideAlerts();
    initializeFormValidation();
    initializeTooltips();
    initializePopovers();
    initializeFavouriteButtons();
    initializeSearchFilters();
    initializeImageGallery();
    initializeScrollAnimations();
}

/* ============================================ */
/* AUTO-HIDE ALERTS                            */
/* ============================================ */

function initializeAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/* ============================================ */
/* FORM VALIDATION                             */
/* ============================================ */

function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });

        // Real-time validation feedback
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });

            input.addEventListener('change', function() {
                validateField(this);
            });
        });
    });
}

/**
 * Validate entire form
 */
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Validate individual field
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.getAttribute('name');
    let isValid = true;

    // Remove previous error message
    const existingError = field.parentElement.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }

    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        showFieldError(field, 'This field is required');
        return isValid;
    }

    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            showFieldError(field, 'Please enter a valid email address');
            return isValid;
        }
    }

    // Password validation (minimum 8 characters)
    if (field.name === 'password' && value && value.length < 8) {
        isValid = false;
        showFieldError(field, 'Password must be at least 8 characters long');
        return isValid;
    }

    // Password confirmation
    if (field.name === 'password_confirm') {
        const passwordField = field.form.querySelector('input[name="password"]');
        if (passwordField && field.value !== passwordField.value) {
            isValid = false;
            showFieldError(field, 'Passwords do not match');
            return isValid;
        }
    }

    // Phone number validation
    if (field.name === 'phone' && value) {
        const phoneRegex = /^[\d\s\-\+\(\)]+$/;
        if (!phoneRegex.test(value) || value.replace(/\D/g, '').length < 10) {
            isValid = false;
            showFieldError(field, 'Please enter a valid phone number');
            return isValid;
        }
    }

    // Mark field as valid
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }

    return isValid;
}

/**
 * Show field error message
 */
function showFieldError(field, message) {
    field.classList.remove('is-valid');
    field.classList.add('is-invalid');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';

    field.parentElement.appendChild(errorDiv);
}

/* ============================================ */
/* BOOTSTRAP TOOLTIPS & POPOVERS                */
/* ============================================ */

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

/* ============================================ */
/* FAVOURITE BUTTONS                           */
/* ============================================ */

function initializeFavouriteButtons() {
    const favouriteButtons = document.querySelectorAll('.btn-favourite');
    
    favouriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            toggleFavourite(this);
        });
    });
}

/**
 * Toggle favourite property
 */
function toggleFavourite(button) {
    const propertyId = button.getAttribute('data-property-id');
    const icon = button.querySelector('i');
    const isFavourited = icon.classList.contains('fas');

    // Animate the button
    button.classList.add('pulse');

    // Make API call (or form submission)
    const url = button.getAttribute('data-action-url') || `/properties/${propertyId}/favourite/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        button.classList.remove('pulse');
        if (data.success) {
            // Toggle heart icon
            if (isFavourited) {
                icon.classList.remove('fas');
                icon.classList.add('far');
                button.classList.remove('btn-danger');
                button.classList.add('btn-outline-danger');
                showNotification('Removed from favourites', 'success');
            } else {
                icon.classList.remove('far');
                icon.classList.add('fas');
                button.classList.remove('btn-outline-danger');
                button.classList.add('btn-danger');
                showNotification('Added to favourites', 'success');
            }
        }
    })
    .catch(error => {
        button.classList.remove('pulse');
        console.error('Error:', error);
        showNotification('Error updating favourite', 'danger');
    });
}

/* ============================================ */
/* SEARCH & FILTERS                            */
/* ============================================ */

function initializeSearchFilters() {
    const searchInputs = document.querySelectorAll('.search-input, .filter-input');
    
    searchInputs.forEach(input => {
        // Debounce search to avoid too many requests
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterProperties();
            }, 500);
        });
    });

    const filterOptions = document.querySelectorAll('.filter-option input');
    filterOptions.forEach(option => {
        option.addEventListener('change', filterProperties);
    });
}

/**
 * Filter properties based on search/filter criteria
 */
function filterProperties() {
    const form = document.querySelector('.search-form');
    if (!form) return;

    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    const currentUrl = window.location.pathname;
    const newUrl = `${currentUrl}?${params.toString()}`;

    // Update URL without page reload
    window.history.pushState({}, '', newUrl);

    // Show loading state (optional)
    const propertyContainer = document.querySelector('.properties-grid, .properties-list');
    if (propertyContainer) {
        propertyContainer.classList.add('loading');
    }

    // Reload results (would need backend support)
    // Or use JavaScript filtering if data is already loaded
}

/* ============================================ */
/* IMAGE GALLERY                               */
/* ============================================ */

function initializeImageGallery() {
    const galleryImages = document.querySelectorAll('[data-gallery="property-gallery"]');
    
    galleryImages.forEach(img => {
        img.addEventListener('click', function() {
            const lightbox = createLightbox(this.src, this.alt);
            document.body.appendChild(lightbox);
        });

        // Lazy load images
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.getAttribute('data-src') || img.src;
                        observer.unobserve(img);
                    }
                });
            });
            observer.observe(img);
        }
    });
}

/**
 * Create lightbox for image viewing
 */
function createLightbox(imageSrc, altText) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn 0.3s ease;
    `;

    const img = document.createElement('img');
    img.src = imageSrc;
    img.alt = altText;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90vh;
        object-fit: contain;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        position: absolute;
        top: 20px;
        right: 30px;
        font-size: 40px;
        font-weight: bold;
        color: white;
        background: none;
        border: none;
        cursor: pointer;
    `;

    closeBtn.addEventListener('click', () => lightbox.remove());
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) lightbox.remove();
    });

    lightbox.appendChild(img);
    lightbox.appendChild(closeBtn);

    return lightbox;
}

/* ============================================ */
/* SCROLL ANIMATIONS                           */
/* ============================================ */

function initializeScrollAnimations() {
    if ('IntersectionObserver' in window) {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe cards for animation
        document.querySelectorAll('.card, .property-card, .stat-card').forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
});

    }
}

/* ============================================ */
/* UTILITY FUNCTIONS                           */
/* ============================================ */

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const alertId = 'notification-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;">
            <i class="fas fa-info-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHtml;
    document.body.appendChild(tempDiv.firstElementChild);

    // Auto close after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Debounce function for optimizing event handlers
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'KSh') {
    return `${currency} ${parseInt(amount).toLocaleString()}`;
}

/**
 * Format date
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

/**
 * Add active class to nav link based on current page
 */
function highlightActiveNavLink() {
    const currentLocation = location.pathname;
    const navLinks = document.querySelectorAll('.navbar a.nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.parentElement.classList.add('active');
        }
    });
}

// Run on page load
document.addEventListener('DOMContentLoaded', highlightActiveNavLink);

/* ============================================ */
/* EXPORT FUNCTIONS                            */
/* ============================================ */

// Make functions globally available if needed
window.toggleFavourite = toggleFavourite;
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.validateField = validateField;
