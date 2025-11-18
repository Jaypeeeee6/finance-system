// ==================== FLASH MESSAGE AUTO-DISMISS ====================
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds (excluding persistent alerts)
    const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const dropdowns = document.querySelectorAll('.new-request-dropdown');
    if (!dropdowns.length) {
        return;
    }

    const closeAll = () => {
        dropdowns.forEach(dropdown => dropdown.classList.remove('open'));
    };

    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.new-request-toggle');
        const links = dropdown.querySelectorAll('.new-request-menu a');
        if (!toggle) {
            return;
        }

        toggle.addEventListener('click', function(event) {
            event.preventDefault();
            const isOpen = dropdown.classList.contains('open');
            closeAll();
            if (!isOpen) {
                dropdown.classList.add('open');
            }
        });

        links.forEach(link => {
            link.addEventListener('click', () => {
                closeAll();
            });
        });
    });

    document.addEventListener('click', function(event) {
        if (!event.target.closest('.new-request-dropdown')) {
            closeAll();
        }
    });
});

// Animation for slide out
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ==================== FORM VALIDATION ====================
// Validate account number (numbers only, max 16 digits)
function validateAccountNumber(input) {
    const value = input.value;
    if (!/^\d*$/.test(value)) {
        input.setCustomValidity('Please enter numbers only');
        return false;
    } else if (value.length > 16) {
        input.setCustomValidity('Account number cannot exceed 16 digits');
        return false;
    } else {
        input.setCustomValidity('');
        return true;
    }
}

// Validate amount (positive numbers)
function validateAmount(input) {
    const value = parseFloat(input.value);
    if (isNaN(value) || value <= 0) {
        input.setCustomValidity('Amount must be greater than 0');
        return false;
    } else {
        input.setCustomValidity('');
        return true;
    }
}

// Add validation to account number fields
document.querySelectorAll('input[name="account_number"]').forEach(input => {
    input.addEventListener('input', function() {
        validateAccountNumber(this);
    });
});

// Add validation to amount fields
document.querySelectorAll('input[name="amount"]').forEach(input => {
    input.addEventListener('input', function() {
        validateAmount(this);
    });
});

// ==================== TABLE SORTING ====================
function sortTable(table, column, asc = true) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const sortedRows = rows.sort((a, b) => {
        const aValue = a.querySelectorAll('td')[column].textContent.trim();
        const bValue = b.querySelectorAll('td')[column].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return asc ? aNum - bNum : bNum - aNum;
        }
        
        // Sort as string
        return asc ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    });
    
    // Remove existing rows
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    // Append sorted rows
    sortedRows.forEach(row => tbody.appendChild(row));
}

// Add click handlers to table headers
document.querySelectorAll('.data-table th').forEach((header, index) => {
    let asc = true;
    header.style.cursor = 'pointer';
    header.addEventListener('click', function() {
        const table = this.closest('table');
        sortTable(table, index, asc);
        asc = !asc;
        
        // Update visual indicator
        document.querySelectorAll('.data-table th').forEach(h => {
            h.style.backgroundColor = '';
        });
        this.style.backgroundColor = '#e9ecef';
    });
});

// ==================== SEARCH/FILTER FUNCTIONALITY ====================
function filterTable(searchInput, table) {
    const filter = searchInput.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(filter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Add search functionality if search input exists
const searchInputs = document.querySelectorAll('[data-search-table]');
searchInputs.forEach(input => {
    const tableId = input.getAttribute('data-search-table');
    const table = document.getElementById(tableId);
    if (table) {
        input.addEventListener('input', function() {
            filterTable(this, table);
        });
    }
});

// ==================== CONFIRM DIALOGS ====================
// Note: Confirmation dialogs are handled by onsubmit attributes in HTML
// No additional JavaScript needed to avoid double alerts

// ==================== FILE UPLOAD PREVIEW ====================
function previewFile(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        const preview = document.createElement('div');
        preview.className = 'file-preview';
        preview.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <small>(${(file.size / 1024).toFixed(2)} KB)</small>
        `;
        
        // Remove existing preview
        const existingPreview = input.parentNode.querySelector('.file-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        input.parentNode.appendChild(preview);
    }
}

// Add file preview to file inputs
document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', function() {
        previewFile(this);
    });
});

// ==================== FORM SUBMIT LOADING STATE ====================
document.querySelectorAll('form').forEach(form => {
    // Skip manager approval forms as they have their own validation
    if (form.action && form.action.includes('manager_approve')) {
        return;
    }
    
    form.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn && !this.hasAttribute('data-no-loading')) {
            // Only show loading state if form will actually submit
            // Check if form has onsubmit that might prevent submission
            const onsubmitAttr = this.getAttribute('onsubmit');
            if (onsubmitAttr && onsubmitAttr.includes('confirm')) {
                // For forms with confirmation, only show loading after confirmation
                const originalSubmit = this.onsubmit;
                this.onsubmit = function() {
                    const result = originalSubmit.call(this);
                    if (result !== false) {
                        // User confirmed, show loading state
                        submitBtn.disabled = true;
                        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    }
                    return result;
                };
            } else {
                // For forms without confirmation, show loading immediately
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        }
    });
});

// ==================== TOOLTIP FUNCTIONALITY ====================
function createTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.85rem;
        z-index: 10000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s;
    `;
    document.body.appendChild(tooltip);
    
    element.addEventListener('mouseenter', function(e) {
        const rect = element.getBoundingClientRect();
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
        tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
        tooltip.style.opacity = '1';
    });
    
    element.addEventListener('mouseleave', function() {
        tooltip.style.opacity = '0';
    });
}

// Add tooltips to elements with title attribute
document.querySelectorAll('[title]').forEach(element => {
    const title = element.getAttribute('title');
    element.removeAttribute('title');
    createTooltip(element, title);
});

// ==================== KEYBOARD SHORTCUTS ====================
document.addEventListener('keydown', function(e) {
    // Ctrl + S to submit form (prevent default save)
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const form = document.querySelector('form');
        if (form) {
            form.submit();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });
    }
});

// ==================== PRINT FUNCTIONALITY ====================
function printReport() {
    window.print();
}

// Add print button functionality
document.querySelectorAll('[data-print]').forEach(button => {
    button.addEventListener('click', printReport);
});

// ==================== EXPORT LOADING ====================
function showExportLoading() {
    // Show loading state for export buttons
    const exportButtons = document.querySelectorAll('#export-pdf-btn, #export-excel-btn');
    exportButtons.forEach(button => {
        const textSpan = button.querySelector('span');
        if (textSpan) {
            textSpan.textContent = 'Exporting...';
            button.disabled = true;
        }
    });
}

// ==================== EXPORT TO CSV ====================
function exportTableToCSV(table, filename = 'report.csv') {
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            return '"' + col.textContent.trim().replace(/"/g, '""') + '"';
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Add export functionality
document.querySelectorAll('[data-export-csv]').forEach(button => {
    button.addEventListener('click', function() {
        const tableId = this.getAttribute('data-export-csv');
        const table = document.getElementById(tableId) || document.querySelector('.data-table');
        if (table) {
            const filename = 'payment_report_' + new Date().toISOString().split('T')[0] + '.csv';
            exportTableToCSV(table, filename);
        }
    });
});

// ==================== REAL-TIME CLOCK ====================
function updateClock() {
    const clockElements = document.querySelectorAll('[data-clock]');
    clockElements.forEach(element => {
        const now = new Date();
        element.textContent = now.toLocaleString();
    });
}

setInterval(updateClock, 1000);
updateClock();

// ==================== SMOOTH SCROLL ====================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ==================== RESPONSIVE NAVIGATION ====================
function toggleMobileNav() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('active');
    }
}

// Add mobile menu toggle if needed
const mobileToggle = document.querySelector('[data-mobile-toggle]');
if (mobileToggle) {
    mobileToggle.addEventListener('click', toggleMobileNav);
}

// ==================== LOADING INDICATOR ====================
let isLoadingShown = false;
let navigationIntentDetected = false;

function showLoading() {
    // Prevent showing loader if already shown or if no navigation intent
    if (isLoadingShown || !navigationIntentDetected) {
        return;
    }
    
    // Double-check that we don't already have a loader
    if (document.getElementById('global-loader')) {
        isLoadingShown = true;
        return;
    }
    
    isLoadingShown = true;
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.dataset.createdAt = Date.now().toString();
    loader.innerHTML = '<div class="spinner"></div>';
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 99999;
    `;
    
    const spinner = loader.querySelector('.spinner');
    spinner.style.cssText = `
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #2196F3;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    `;
    
    // Add spin animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(loader);
}

function hideLoading() {
    isLoadingShown = false;
    navigationIntentDetected = false;
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}

// Track user navigation intent (clicks on links, form submissions, etc.)
document.addEventListener('click', function(e) {
    const target = e.target;
    // Check if clicking on a link that navigates away
    if (target.tagName === 'A' && target.href && !target.href.startsWith('javascript:') && !target.hasAttribute('download')) {
        const currentHost = window.location.host;
        const linkHost = new URL(target.href, window.location.href).host;
        // Only set navigation intent for external links or links that change the page
        if (linkHost !== currentHost || target.target === '_blank') {
            navigationIntentDetected = true;
        } else {
            // For same-origin links, check if it's actually a navigation
            const currentPath = window.location.pathname;
            const linkPath = new URL(target.href, window.location.href).pathname;
            if (linkPath !== currentPath) {
                navigationIntentDetected = true;
            }
        }
    }
}, true); // Use capture phase to catch all clicks

// Track form submissions
document.addEventListener('submit', function(e) {
    const form = e.target;
    // Only show loading for forms that actually submit (not AJAX forms)
    if (form.tagName === 'FORM' && !form.hasAttribute('data-no-loading')) {
        navigationIntentDetected = true;
    }
}, true);

// Reset navigation intent after a short delay (in case beforeunload doesn't fire)
setTimeout(function() {
    navigationIntentDetected = false;
}, 100);

// Show loading on page navigation, but only if navigation was intentional
window.addEventListener('beforeunload', function(e) {
    // Only show loading if we detected actual navigation intent
    // AND the event is actually a navigation (not just browser optimization)
    if (navigationIntentDetected) {
        showLoading();
    }
});

// Auto-hide loading if page becomes visible again (user came back)
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // Hide any stuck loaders when user returns to tab
        hideLoading();
    }
});

// Hide loading on page load (in case it got stuck)
document.addEventListener('DOMContentLoaded', function() {
    hideLoading();
});

// Additional safety: Hide loading if it's been visible for more than 5 seconds
setInterval(function() {
    const loader = document.getElementById('global-loader');
    if (loader && isLoadingShown) {
        const createdAt = parseInt(loader.dataset.createdAt || '0');
        if (createdAt > 0) {
            const loaderAge = Date.now() - createdAt;
            if (loaderAge > 5000) {
                console.warn('Loading indicator was visible for too long, hiding it');
                hideLoading();
            }
        }
    }
}, 1000);

// ==================== DATA VALIDATION HELPERS ====================
// Email validation
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Phone validation
function isValidPhone(phone) {
    return /^\d{10,}$/.test(phone.replace(/\D/g, ''));
}

// Date validation
function isValidDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
}

// ==================== CONSOLE WELCOME MESSAGE ====================
console.log('%c Payment Request Management System ', 'background: #2196F3; color: white; font-size: 20px; padding: 10px;');
console.log('%c Built with Flask & JavaScript ', 'background: #4CAF50; color: white; font-size: 14px; padding: 5px;');
console.log('%c For support, contact your IT administrator ', 'font-size: 12px; color: #666;');

