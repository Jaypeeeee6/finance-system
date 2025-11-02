/**
 * Real-time WebSocket Updates for Payment Request System
 * Instant updates when new requests are submitted - NO REFRESH NEEDED!
 */

// Socket.IO connection
let socket = null;

// Track original title and unread count for tab badge
let originalTitle = document.title;
let unreadTotal = 0;
function updateTabTitle() {
    document.title = unreadTotal > 0 ? `(${unreadTotal}) ${originalTitle}` : originalTitle;
}

// Fetch unread count from server and sync tab title
function syncTabTitleFromServer() {
    fetch('/api/notifications/unread_count')
        .then(response => response.json())
        .then(data => {
            unreadTotal = typeof data.count === 'number' ? data.count : 0;
            updateTabTitle();
        })
        .catch(() => {
            // Silently ignore errors syncing the tab title
        });
}

/**
 * Initialize real-time WebSocket connection
 */
function initRealTimeUpdates() {
    // Connect to Socket.IO server
    socket = io();
    
    // Listen for connection
    socket.on('connect', function() {
        console.log('%c WebSocket Connected ', 'background: #4CAF50; color: white; font-weight: bold; padding: 5px;');
        updateConnectionStatus(true);
        
        // Join appropriate room based on user role
        const userRole = document.body.getAttribute('data-user-role');
        console.log('🔔 DEBUG: User role detected:', userRole);
        
        // All users join the general room
        socket.emit('join_room', { room: 'all_users' });
        console.log('🔔 DEBUG: Joined all_users room');
        
        // Role-specific rooms for targeted notifications
        if (userRole === 'Finance Staff' || userRole === 'Finance Admin') {
            socket.emit('join_room', { room: 'finance_admin' });
            console.log('🔔 DEBUG: Joined finance_admin room for real-time updates');
        } else if (userRole === 'GM') {
            socket.emit('join_room', { room: 'gm' });
        } else if (userRole === 'Operation Manager') {
            socket.emit('join_room', { room: 'operation_manager' });
        } else if (userRole === 'IT Staff') {
            socket.emit('join_room', { room: 'it_staff' });
        } else if (userRole === 'Department Manager') {
            socket.emit('join_room', { room: 'department_managers' });
            console.log('🔔 DEBUG: Joined department_managers room for real-time updates');
        } else if (userRole === 'Project Staff') {
            socket.emit('join_room', { room: 'project_staff' });
        } else if (userRole && userRole.endsWith(' Staff')) {
            // All Staff roles (including PR Staff, HR Staff, etc.) join department_staff room
            socket.emit('join_room', { room: 'department_staff' });
            console.log('🔔 DEBUG: Joined department_staff room for real-time updates');
        }
        
        console.log(`🔔 DEBUG: User role: ${userRole} - Joined real-time notification rooms`);
    });

    // Maintenance mode updates
    socket.on('maintenance_update', function(state) {
        try {
            const dept = document.body.getAttribute('data-user-department');
            const isIT = dept === 'IT';
            if (!state) return;
            if (state.enabled) {
                if (isIT) {
                    const banner = document.getElementById('maintenance-banner');
                    if (banner) banner.style.display = 'block';
                } else {
                    window.location.reload();
                }
            } else {
                if (isIT) {
                    const banner = document.getElementById('maintenance-banner');
                    if (banner) banner.style.display = 'none';
                } else {
                    // Bring users back if they were on maintenance page
                    window.location.reload();
                }
            }
        } catch (e) {
            console.error('maintenance_update handling error', e);
        }
    });
    
    // Listen for disconnection
    socket.on('disconnect', function() {
        console.log('%c WebSocket Disconnected ', 'background: #f44336; color: white; font-weight: bold; padding: 5px;');
        updateConnectionStatus(false);
    });
    
    // Listen for new payment requests
    socket.on('new_request', function(data) {
        console.log('🔔 DEBUG: New payment request received:', data);
        console.log('🔔 DEBUG: Current user role:', document.body.getAttribute('data-user-role'));
        console.log('🔔 DEBUG: Current page:', window.location.pathname);
        handleNewRequest(data);
        // Update notification count when new request is created
        updateNotificationCount();
        // Also sync tab title badge
        syncTabTitleFromServer();
    });
    
    // Listen for request updates (approval/pending)
    socket.on('request_updated', function(data) {
        console.log('Payment request updated:', data);
        handleRequestUpdate(data);
        // Update notification count when request is updated
        updateNotificationCount();
        // Also sync tab title badge
        syncTabTitleFromServer();
    });
    
    // Listen for new notifications
    socket.on('new_notification', function(data) {
        console.log('New notification received:', data);
        handleNewNotification(data);
        // Ensure tab title reflects newest count
        syncTabTitleFromServer();
    });
    
    // Listen for notification updates (triggers badge update)
    socket.on('notification_update', function(data) {
        console.log('🔔 DEBUG: Notification update received:', data);
        // Force update notification count
        updateNotificationCount();
        // Also sync tab title badge
        syncTabTitleFromServer();
        
        // Also refresh dropdown if it's open
        if (typeof notificationDropdownOpen !== 'undefined' && notificationDropdownOpen) {
            console.log('🔔 DEBUG: Dropdown is open, refreshing due to notification_update');
            if (typeof loadNotifications === 'function') {
                loadNotifications();
            }
        }
    });
    
    // Add visual indicator
    addRefreshIndicator();

    // Polling fallback each 5s to ensure clients react even if sockets fail
    try {
        setInterval(function(){
            fetch('/maintenance/public_status')
                .then(r=>r.json())
                .then(s=>{
                    if (!s) return;
                    const dept = document.body.getAttribute('data-user-department');
                    const isIT = dept === 'IT';
                    const onMaintPage = !!document.getElementById('maintenance-page');
                    if (s.enabled) {
                        if (!isIT) {
                            window.location.reload();
                        } else {
                            const banner = document.getElementById('maintenance-banner');
                            if (banner) banner.style.display = 'block';
                        }
                    } else {
                        // If maintenance turned off while user is on maintenance page, bring them back
                        if (onMaintPage) {
                            window.location.reload();
                        } else if (isIT) {
                            const banner = document.getElementById('maintenance-banner');
                            if (banner) banner.style.display = 'none';
                        }
                    }
                })
                .catch(()=>{});
        }, 5000);
    } catch (e) { /* ignore */ }
}

/**
 * Handle new payment request from WebSocket
 */
function handleNewRequest(data) {
    console.log('🔔 DEBUG: handleNewRequest called with:', data);
    
    // Show notification
    showNewRequestNotification(1, data);
    
    // Update notification count immediately
    updateNotificationCount();
    
    // Don't update dashboard table immediately if we just submitted a form (to avoid permission errors during redirect)
    // Only update if we're already on a dashboard page, not during redirects
    const currentPath = window.location.pathname;
    if (currentPath.includes('/dashboard') || 
        currentPath.includes('/finance') || 
        currentPath.includes('/admin') || 
        currentPath.includes('/it') || 
        currentPath.includes('/gm') || 
        currentPath.includes('/operation') || 
        currentPath.includes('/project') ||
        currentPath.includes('/department') ||
        currentPath.includes('/ceo')) {
        // Update dashboard table dynamically with delay to ensure redirect is complete
        setTimeout(() => {
            updateDashboardTable();
        }, 2000); // Increased delay to ensure redirect completes
    }
}

/**
 * Handle request update from WebSocket
 */
function handleRequestUpdate(data) {
    console.log('🔔 DEBUG: handleRequestUpdate called with:', data);
    
    // Show update notification
    showUpdateNotification(data);
    
    // Only update dashboard if we're not on a request page
    const currentPath = window.location.pathname;
    if (!currentPath.includes('/request/')) {
        // Update dashboard table dynamically
        updateDashboardTable();
        
        // Force a small delay to ensure the server has processed the update
        setTimeout(() => {
            updateDashboardTable();
        }, 1000);
    } else {
        console.log('🔔 DEBUG: Skipping dashboard update - on request page');
    }
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const indicator = document.querySelector('.refresh-indicator');
    if (indicator) {
        const statusText = indicator.querySelector('strong');
        if (statusText) {
            statusText.textContent = connected ? 'LIVE' : 'OFFLINE';
            statusText.style.color = connected ? '#4CAF50' : '#f44336';
        }
    }
}

/**
 * Show notification for new requests
 * NOTE: Visual pop-ups removed - only sound notification kept
 */
function showNewRequestNotification(count, data) {
    // Play notification sound only (no visual pop-up)
    playNotificationSound();
}

/**
 * Show notification for request updates
 * NOTE: Visual pop-ups removed - only sound notification kept
 */
function showUpdateNotification(data) {
    // Play notification sound only (no visual pop-up)
    playNotificationSound();
}

/**
 * Play a subtle notification sound
 */
function playNotificationSound() {
    // Create a simple beep sound using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (e) {
        // Silently fail if audio is not supported
    }
}

// WebSocket connection management - no polling needed!

/**
 * Add refresh indicator to the page
 */
function addRefreshIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'refresh-indicator';
    indicator.innerHTML = `
        <i class="fas fa-bolt"></i>
        <span>Real-Time: <strong>LIVE</strong></span>
    `;
    
    // Add to dashboard header if it exists
    const dashboardHeader = document.querySelector('.dashboard-header');
    if (dashboardHeader) {
        // Find the header content area and add the indicator there
        const headerContent = dashboardHeader.querySelector('h1') || dashboardHeader.querySelector('.dashboard-title');
        if (headerContent) {
            headerContent.appendChild(indicator);
        } else {
            dashboardHeader.appendChild(indicator);
        }
    }
}

// Real-time indicator is always live - no timestamp needed

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize real-time updates on ALL pages for ALL roles
    initRealTimeUpdates();
    
    // Update notification badge on page load
    if (window.updateNotificationBadge) {
        window.updateNotificationBadge();
    }
    // Always sync tab title count on load
    syncTabTitleFromServer();
    
    console.log('%c Real-Time WebSocket Active for ALL ROLES ', 'background: #4CAF50; color: white; font-weight: bold; padding: 5px;');
    console.log('Instant updates - No refresh needed!');
    console.log('Works for: Finance Admin, Finance Staff, GM, Operation Manager, IT Staff, Department Manager, Project Staff, and all other roles');
});

/**
 * Handle new notification from WebSocket
 */
function handleNewNotification(data) {
    console.log('🔔 DEBUG: handleNewNotification called with:', data);
    
    // Play notification sound for notification bell
    playNotificationSound();
    
    // Update notification count
    updateNotificationCount();
    
    // Update notification dropdown if it's open
    if (notificationDropdownOpen) {
        console.log('🔔 DEBUG: Dropdown is open, refreshing notifications');
        loadNotifications();
    }
    
    // Refresh notifications if on notifications page
    if (window.location.pathname.includes('/notifications')) {
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
}

/**
 * Play notification sound when new notification arrives
 * Uses Web Audio API to generate a simple bell notification sound
 */
function playNotificationSound() {
    try {
        // Check if user wants sounds (could be extended with user preference)
        // For now, always play sound
        
        // Use Web Audio API to generate a pleasant notification sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create a simple two-tone bell sound
        const oscillator1 = audioContext.createOscillator();
        const oscillator2 = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        // Connect oscillators to gain node
        oscillator1.connect(gainNode);
        oscillator2.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Configure first tone (higher frequency)
        oscillator1.type = 'sine';
        oscillator1.frequency.value = 800; // 800 Hz
        
        // Configure second tone (lower frequency)
        oscillator2.type = 'sine';
        oscillator2.frequency.value = 600; // 600 Hz
        
        // Configure gain envelope (fade out)
        const now = audioContext.currentTime;
        gainNode.gain.setValueAtTime(0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        
        // Play the sound
        oscillator1.start(now);
        oscillator2.start(now);
        oscillator1.stop(now + 0.3);
        oscillator2.stop(now + 0.3);
    } catch (error) {
        console.log('Error playing notification sound:', error);
        // Fallback: try simple beep
        try {
            const audio = new Audio();
            audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPRgjMGHm7A7+OZUxEKUaTi8LhnIAUxgc/y1IM1Bh9uve/jmFMRClGj4O+4ZSAGMYHP8tSCNQYebsDv45lTEQpRo+PwuGcgBjGBz/LUgzUGH27A7+OZUxEKUaPg77hlIAYxgc/y1II1Bh5uwO/jmVM';
            audio.volume = 0.3;
            audio.play().catch(err => console.log('Fallback audio play failed:', err));
        } catch (fallbackError) {
            console.log('All audio methods failed:', fallbackError);
        }
    }
}

/**
 * Update notification count in navigation
 */
function updateNotificationCount() {
    // Use the global function from base.html if available
    if (window.updateNotificationBadge) {
        window.updateNotificationBadge();
    } else {
        // Fallback to direct API call
        fetch('/api/notifications/unread_count')
            .then(response => response.json())
            .then(data => {
                // Update notification badge in navigation bell
                const navBadge = document.getElementById('nav-notification-badge');
                if (navBadge) {
                    if (data.count > 0) {
                        navBadge.textContent = data.count;
                        navBadge.style.display = 'flex';
                    } else {
                        navBadge.style.display = 'none';
                    }
                }
                
                // Also update any other notification badges
                const navLink = document.querySelector('a[href*="notifications"]');
                if (navLink) {
                    let badge = navLink.querySelector('.notification-badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'notification-badge';
                        navLink.appendChild(badge);
                    }
                    
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'inline';
                    } else {
                        badge.style.display = 'none';
                    }
                }

                // Update tab title badge using the latest count
                unreadTotal = typeof data.count === 'number' ? data.count : 0;
                updateTabTitle();
            })
            .catch(error => {
                console.error('Error updating notification count:', error);
            });
    }
}

/**
 * Update dashboard table dynamically without page refresh
 */
function updateDashboardTable() {
    // Get current page URL to determine which dashboard to update
    const currentPath = window.location.pathname;
    
    // Only update if we're on a dashboard page, NOT on individual request pages
    if (!currentPath.includes('/finance') && 
        !currentPath.includes('/admin') && 
        !currentPath.includes('/it') && 
        !currentPath.includes('/gm') && 
        !currentPath.includes('/operation') && 
        !currentPath.includes('/project') &&
        !currentPath.includes('/department') &&
        !currentPath.includes('/ceo')) {
        return;
    }
    
    // Don't update if we're on an individual request page (like /request/123)
    if (currentPath.includes('/request/')) {
        return;
    }
    
    // Don't fetch if we're on the main /dashboard route (which redirects) - wait until we're on actual dashboard
    if (currentPath === '/dashboard' || currentPath === '/dashboard/') {
        return; // Skip update during redirect
    }
    
    // Preserve current URL parameters
    const currentUrl = new URL(window.location);
    const params = new URLSearchParams(currentUrl.search);
    
    // Fetch updated data from the current page with same parameters
    fetch(window.location.href)
        .then(response => {
            // Check if response is OK, if not, don't try to parse
            if (!response.ok && (response.status === 403 || response.status === 401)) {
                console.log('Dashboard update skipped - permission issue');
                return null;
            }
            return response.text();
        })
        .then(html => {
            if (!html) return; // Skip if we got null from permission check
            // Parse the response and extract the table content
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Get the active tab
            const activeTab = getActiveTab();
            if (!activeTab) return;
            
            // Find the table in the active tab
            const newTable = doc.querySelector(`#tab-content-${activeTab} .data-table`);
            const newPagination = doc.querySelector('.pagination-container');
            
            if (newTable) {
                // Update the table content in the active tab
                const currentTable = document.querySelector(`#tab-content-${activeTab} .data-table`);
                if (currentTable) {
                    currentTable.innerHTML = newTable.innerHTML;
                }
                
                // Update pagination if it exists
                if (newPagination) {
                    const currentPagination = document.querySelector('.pagination-container');
                    if (currentPagination) {
                        currentPagination.innerHTML = newPagination.innerHTML;
                    }
                }
                
                // Re-apply any active filters
                if (typeof filterTable === 'function') {
                    filterTable();
                }
                
                // Add visual indicator that table was updated
                showTableUpdateIndicator();
                
                console.log('Dashboard table updated successfully');
            }
        })
        .catch(error => {
            console.error('Error updating dashboard:', error);
            // Don't reload the page, just log the error
            console.log('Continuing with current data...');
        });
}

/**
 * Get the currently active tab
 */
function getActiveTab() {
    const activeTabButton = document.querySelector('.tab-button.active');
    if (activeTabButton) {
        const onclick = activeTabButton.getAttribute('onclick');
        if (onclick) {
            const match = onclick.match(/switchTab\('([^']+)'\)/);
            if (match) {
                return match[1];
            }
        }
    }
    
    // Fallback: check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('tab') || 'pending';
}

/**
 * Show visual indicator that table was updated
 */
function showTableUpdateIndicator() {
    // Add a subtle visual indicator that the table was updated
    const table = document.querySelector('.data-table');
    if (table) {
        // Add a temporary highlight effect
        table.style.transition = 'background-color 0.3s ease';
        table.style.backgroundColor = '#f8f9fa';
        
        setTimeout(() => {
            table.style.backgroundColor = '';
        }, 1000);
    }
    
    // Visual notification removed - table update happens silently
}


/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.disconnect();
    }
});

// Refresh count when tab gains focus
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        syncTabTitleFromServer();
    }
});



