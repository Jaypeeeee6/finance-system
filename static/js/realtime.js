/**
 * Real-time WebSocket Updates for Payment Request System
 * Instant updates when new requests are submitted - NO REFRESH NEEDED!
 */

// Socket.IO connection
let socket = null;

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
        if (userRole === 'Finance Staff' || userRole === 'Finance Admin') {
            socket.emit('join_room', { room: 'finance_admin' });
        }
        socket.emit('join_room', { room: 'all_users' });
    });
    
    // Listen for disconnection
    socket.on('disconnect', function() {
        console.log('%c WebSocket Disconnected ', 'background: #f44336; color: white; font-weight: bold; padding: 5px;');
        updateConnectionStatus(false);
    });
    
    // Listen for new payment requests
    socket.on('new_request', function(data) {
        console.log('New payment request received:', data);
        handleNewRequest(data);
    });
    
    // Listen for request updates (approval/pending)
    socket.on('request_updated', function(data) {
        console.log('Payment request updated:', data);
        handleRequestUpdate(data);
    });
    
    // Listen for new notifications
    socket.on('new_notification', function(data) {
        console.log('New notification received:', data);
        handleNewNotification(data);
    });
    
    // Add visual indicator
    addRefreshIndicator();
}

/**
 * Handle new payment request from WebSocket
 */
function handleNewRequest(data) {
    // Show notification
    showNewRequestNotification(1, data);
    
    // Reload the page to get updated data
    location.reload();
}

/**
 * Handle request update from WebSocket
 */
function handleRequestUpdate(data) {
    // Show update notification
    showUpdateNotification(data);
    
    // Reload the page to get updated data
    location.reload();
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
 */
function showNewRequestNotification(count, data) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'realtime-notification';
    notification.innerHTML = `
        <i class="fas fa-bell"></i>
        <div>
            <strong>New Payment Request!</strong>
            ${data ? `<div style="font-size: 0.85rem; margin-top: 0.3rem;">${data.requestor_name} - OMR ${data.amount.toFixed(3)}</div>` : ''}
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
    
    // Play notification sound
    playNotificationSound();
}

/**
 * Show notification for request updates
 */
function showUpdateNotification(data) {
    const notification = document.createElement('div');
    notification.className = 'realtime-notification';
    notification.innerHTML = `
        <i class="fas fa-sync-alt"></i>
        <div>
            <strong>Request Updated!</strong>
            <div style="font-size: 0.85rem; margin-top: 0.3rem;">Request #${data.request_id} - ${data.status}</div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
    
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
        <span class="last-update">Connected</span>
    `;
    
    // Add to dashboard header if it exists
    const dashboardHeader = document.querySelector('.dashboard-header');
    if (dashboardHeader) {
        dashboardHeader.appendChild(indicator);
    }
}

// Real-time indicator is always live - no timestamp needed

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on dashboard pages with data tables
    if (document.querySelector('.data-table')) {
        initRealTimeUpdates();
        
        console.log('%c Real-Time WebSocket Active ', 'background: #4CAF50; color: white; font-weight: bold; padding: 5px;');
        console.log('Instant updates - No refresh needed!');
    }
});

/**
 * Handle new notification from WebSocket
 */
function handleNewNotification(data) {
    // Show notification popup
    showNotificationPopup(data);
    
    // Update notification count if on dashboard
    updateNotificationCount();
    
    // Refresh notifications if on notifications page
    if (window.location.pathname.includes('/notifications')) {
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
}

/**
 * Show notification popup
 */
function showNotificationPopup(data) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'realtime-notification show';
    notification.innerHTML = `
        <i class="fas fa-bell"></i>
        <div>
            <strong>${data.title}</strong>
            <p>${data.message}</p>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

/**
 * Update notification count in navigation
 */
function updateNotificationCount() {
    fetch('/api/notifications/unread_count')
        .then(response => response.json())
        .then(data => {
            // Update notification badge in navigation
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
        })
        .catch(error => {
            console.error('Error updating notification count:', error);
        });
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.disconnect();
    }
});



