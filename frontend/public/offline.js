// Page hors ligne. Script dans un fichier : la CSP de la page n'autorise
// aucun script inline (audit INFO-3).
// Auto-reload when connectivity is restored
window.addEventListener('online', () => {
  window.location.reload();
});

// Show current connectivity status
function updateStatus() {
  document.querySelector('.status-dot').style.background =
    navigator.onLine ? '#10b981' : '#ef4444';
}
window.addEventListener('online',  updateStatus);
window.addEventListener('offline', updateStatus);
updateStatus();

document.getElementById('reessayer').addEventListener('click', () => window.location.reload());
