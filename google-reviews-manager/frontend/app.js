// Application JavaScript
// Détection automatique de l'URL de l'API
// En développement local, utilise localhost:8000
// En production, l'API doit être accessible depuis le navigateur (pas depuis le conteneur)
const API_URL = (() => {
    // Si on accède via localhost, utiliser localhost pour l'API aussi
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    // En production, utiliser le même hostname avec le port 8000
    // ou configurer un reverse proxy
    return `${window.location.protocol}//${hostname}:8000`;
})();

// Check API health status
async function checkHealth() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            statusIndicator.classList.add('connected');
            statusIndicator.classList.remove('disconnected');
            statusText.textContent = 'Connexion au serveur réussie ✓';
        } else {
            throw new Error('Status not ok');
        }
    } catch (error) {
        statusIndicator.classList.add('disconnected');
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Impossible de se connecter au serveur ✗';
        console.error('Health check failed:', error);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    
    // Check health every 30 seconds
    setInterval(checkHealth, 30000);
});
