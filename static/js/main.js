/* HomeFinder Portal – Main JS */

// Notification badge counter
async function updateNotifBadge() {
  try {
    const res  = await fetch('/api/notifications/count');
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById('notif-count');
    if (badge) {
      if (data.count > 0) {
        badge.textContent = data.count > 9 ? '9+' : data.count;
        badge.classList.remove('d-none');
      } else {
        badge.classList.add('d-none');
      }
    }
  } catch (_) {}
}

// Auto-dismiss alerts after 5 seconds
function autoDismissAlerts() {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
}

// Image lazy loading fallback
function setupImageFallbacks() {
  document.querySelectorAll('img[onerror]').forEach(img => {
    img.addEventListener('error', function() {
      this.src = 'https://via.placeholder.com/400x250?text=HomeFinder';
    });
  });
}

// Confirm delete actions
function confirmDelete(form) {
  return confirm('Are you sure you want to delete this? This action cannot be undone.');
}

document.addEventListener('DOMContentLoaded', () => {
  updateNotifBadge();
  autoDismissAlerts();
  setupImageFallbacks();

  // Refresh notification count every 30 seconds
  setInterval(updateNotifBadge, 30000);
});
