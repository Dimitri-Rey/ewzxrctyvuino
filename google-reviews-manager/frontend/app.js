// API Client
class ApiClient {
    constructor() {
        // Utilise le proxy nginx pour accéder au backend
        // En développement local sans Docker, utiliser directement le backend
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // Si on est sur le port 8080, utiliser le proxy nginx
            if (window.location.port === '8080' || window.location.port === '') {
                this.baseURL = '/api';
            } else {
                // Développement local direct
                this.baseURL = 'http://localhost:8000';
            }
        } else {
            // Production : utiliser le proxy nginx
            this.baseURL = '/api';
        }
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Application
const app = {
    api: new ApiClient(),
    currentPendingReplyId: null,
    accounts: [],
    locations: [],
    reviews: [],
    templates: [],
    pendingReplies: [],

    // Initialization
    init() {
        this.setupNavigation();
        this.checkHealth();
        this.loadDashboard();
        setInterval(() => this.checkHealth(), 30000);
    },

    // Navigation
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.showSection(section);
            });
        });

        const navToggle = document.getElementById('navToggle');
        if (navToggle) {
            navToggle.addEventListener('click', () => {
                document.getElementById('navMenu').classList.toggle('active');
            });
        }
    },

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // Show selected section
        const section = document.getElementById(sectionName);
        if (section) {
            section.classList.add('active');
        }

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === sectionName) {
                link.classList.add('active');
            }
        });

        // Load section data
        switch(sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'accounts':
                this.loadAccounts();
                break;
            case 'locations':
                this.loadLocations();
                break;
            case 'reviews':
                this.loadReviews();
                break;
            case 'templates':
                this.loadTemplates();
                break;
            case 'pending':
                this.loadPendingReplies();
                break;
        }
    },

    // Health Check
    async checkHealth() {
        try {
            const data = await this.api.get('/health');
            const indicator = document.getElementById('statusIndicator');
            if (indicator) {
                indicator.classList.toggle('connected', data.status === 'ok');
            }
        } catch (error) {
            const indicator = document.getElementById('statusIndicator');
            if (indicator) {
                indicator.classList.remove('connected');
            }
        }
    },

    // Dashboard
    async loadDashboard() {
        try {
            const [accounts, locations, pendingReplies] = await Promise.all([
                this.api.get('/auth/accounts'),
                this.api.get('/locations'),
                this.api.get('/replies/pending')
            ]);

            // Count reviews
            let reviewsCount = 0;
            for (const location of locations) {
                try {
                    const reviews = await this.api.get(`/locations/${location.id}/reviews`);
                    reviewsCount += reviews.length;
                } catch (e) {
                    // Ignore errors
                }
            }

            document.getElementById('accountsCount').textContent = accounts.length;
            document.getElementById('locationsCount').textContent = locations.length;
            document.getElementById('reviewsCount').textContent = reviewsCount;
            document.getElementById('pendingCount').textContent = pendingReplies.length;
        } catch (error) {
            this.showToast('Erreur lors du chargement du dashboard', 'error');
        }
    },

    async refreshAll() {
        this.showToast('Actualisation en cours...', 'info');
        await this.loadDashboard();
        this.showToast('Données actualisées', 'success');
    },

    // Accounts
    async loadAccounts() {
        const container = document.getElementById('accountsList');
        container.innerHTML = '<div class="loading">Chargement...</div>';

        try {
            const accounts = await this.api.get('/auth/accounts');
            this.accounts = accounts;

            if (accounts.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">👤</div>
                        <p>Aucun compte connecté</p>
                        <button class="btn btn-primary" onclick="app.connectAccount()" style="margin-top: 1rem;">
                            Connecter un compte Google
                        </button>
                    </div>
                `;
                return;
            }

            container.innerHTML = accounts.map(account => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${this.escapeHtml(account.google_email)}</div>
                            <div class="card-subtitle">Connecté le ${new Date(account.created_at).toLocaleDateString('fr-FR')}</div>
                        </div>
                    </div>
                    <div class="review-actions">
                        <button class="btn btn-danger btn-sm" onclick="app.disconnectAccount(${account.id})">
                            Déconnecter
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = `<div class="empty-state">Erreur: ${error.message}</div>`;
        }
    },

    connectAccount() {
        // Utiliser le proxy nginx pour la redirection OAuth
        const authURL = this.api.baseURL === '/api' ? '/auth/login' : `${this.api.baseURL}/auth/login`;
        window.location.href = authURL;
    },

    async disconnectAccount(accountId) {
        if (!confirm('Êtes-vous sûr de vouloir déconnecter ce compte ?')) {
            return;
        }

        try {
            await this.api.delete(`/auth/accounts/${accountId}`);
            this.showToast('Compte déconnecté', 'success');
            this.loadAccounts();
            this.loadDashboard();
        } catch (error) {
            this.showToast('Erreur lors de la déconnexion', 'error');
        }
    },

    // Locations
    async loadLocations() {
        const container = document.getElementById('locationsList');
        container.innerHTML = '<div class="loading">Chargement...</div>';

        try {
            const locations = await this.api.get('/locations');
            this.locations = locations;

            // Update account filter
            const accountFilter = document.getElementById('locationAccountFilter');
            if (accountFilter) {
                const accounts = await this.api.get('/auth/accounts');
                accountFilter.innerHTML = '<option value="">Tous les comptes</option>' +
                    accounts.map(acc => `<option value="${acc.id}">${this.escapeHtml(acc.google_email)}</option>`).join('');
            }

            if (locations.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📍</div>
                        <p>Aucun établissement trouvé</p>
                        <p style="margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
                            Connectez un compte et synchronisez les établissements
                        </p>
                    </div>
                `;
                return;
            }

            container.innerHTML = locations.map(location => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${this.escapeHtml(location.name)}</div>
                            <div class="card-subtitle">${this.escapeHtml(location.address || 'Adresse non disponible')}</div>
                        </div>
                    </div>
                    <div class="review-actions">
                        <button class="btn btn-secondary btn-sm" onclick="app.syncLocation(${location.account_id})">
                            🔄 Synchroniser
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="app.showLocationReviews(${location.id})">
                            Voir les avis
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = `<div class="empty-state">Erreur: ${error.message}</div>`;
        }
    },

    async syncLocation(accountId) {
        try {
            this.showToast('Synchronisation en cours...', 'info');
            await this.api.post(`/locations/${accountId}/sync`);
            this.showToast('Établissements synchronisés', 'success');
            this.loadLocations();
        } catch (error) {
            this.showToast('Erreur lors de la synchronisation', 'error');
        }
    },

    async syncAllLocations() {
        try {
            const accounts = await this.api.get('/auth/accounts');
            for (const account of accounts) {
                await this.syncLocation(account.id);
            }
        } catch (error) {
            this.showToast('Erreur lors de la synchronisation', 'error');
        }
    },

    // Reviews
    async loadReviews() {
        const container = document.getElementById('reviewsList');
        container.innerHTML = '<div class="loading">Chargement...</div>';

        try {
            // Load locations for filter
            const locations = await this.api.get('/locations');
            const locationFilter = document.getElementById('reviewLocationFilter');
            if (locationFilter) {
                locationFilter.innerHTML = '<option value="">Tous les établissements</option>' +
                    locations.map(loc => `<option value="${loc.id}">${this.escapeHtml(loc.name)}</option>`).join('');
                locationFilter.addEventListener('change', () => this.filterReviews());
            }

            // Load all reviews
            this.reviews = [];
            for (const location of locations) {
                try {
                    const reviews = await this.api.get(`/locations/${location.id}/reviews`);
                    reviews.forEach(review => {
                        review.location_name = location.name;
                        review.location_id = location.id;
                    });
                    this.reviews.push(...reviews);
                } catch (e) {
                    // Ignore errors
                }
            }

            this.filterReviews();
        } catch (error) {
            container.innerHTML = `<div class="empty-state">Erreur: ${error.message}</div>`;
        }
    },

    filterReviews() {
        const container = document.getElementById('reviewsList');
        const locationFilter = document.getElementById('reviewLocationFilter')?.value || '';
        const ratingFilter = document.getElementById('reviewRatingFilter')?.value || '';
        const replyFilter = document.getElementById('reviewReplyFilter')?.value || '';

        let filtered = [...this.reviews];

        if (locationFilter) {
            filtered = filtered.filter(r => r.location_id === parseInt(locationFilter));
        }

        if (ratingFilter) {
            filtered = filtered.filter(r => r.rating === parseInt(ratingFilter));
        }

        if (replyFilter === 'replied') {
            filtered = filtered.filter(r => r.reply);
        } else if (replyFilter === 'no-reply') {
            filtered = filtered.filter(r => !r.reply);
        }

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⭐</div>
                    <p>Aucun avis trouvé</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(review => `
            <div class="review-card">
                <div class="review-header">
                    <div>
                        <div class="review-author">${this.escapeHtml(review.author_name)}</div>
                        <div style="font-size: 0.9rem; color: var(--text-muted); margin-top: 0.25rem;">
                            ${this.escapeHtml(review.location_name)} • ${new Date(review.created_at).toLocaleDateString('fr-FR')}
                        </div>
                    </div>
                    <span class="rating-badge rating-${review.rating}">${review.rating}★</span>
                </div>
                ${review.comment ? `<p class="review-comment">${this.escapeHtml(review.comment)}</p>` : ''}
                ${review.reply ? `
                    <div class="review-reply">
                        <strong>Réponse:</strong>
                        <p>${this.escapeHtml(review.reply)}</p>
                    </div>
                ` : ''}
                <div class="review-actions">
                    ${!review.reply ? `
                        <button class="btn btn-primary btn-sm" onclick="app.suggestReply(${review.id})">
                            💬 Suggérer une réponse
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    },

    async showLocationReviews(locationId) {
        this.showSection('reviews');
        document.getElementById('reviewLocationFilter').value = locationId;
        await this.loadReviews();
    },

    async suggestReply(reviewId) {
        try {
            this.showToast('Génération de la suggestion...', 'info');
            const result = await this.api.post(`/replies/reviews/${reviewId}/suggest-reply`);
            this.showToast('Suggestion générée', 'success');
            this.loadPendingReplies();
            this.showSection('pending');
        } catch (error) {
            this.showToast('Erreur lors de la génération', 'error');
        }
    },

    // Templates
    async loadTemplates() {
        const container = document.getElementById('templatesList');
        container.innerHTML = '<div class="loading">Chargement...</div>';

        try {
            const templates = await this.api.get('/templates');
            this.templates = templates;

            if (templates.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📝</div>
                        <p>Aucun template</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = templates.map(template => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${this.escapeHtml(template.name)}</div>
                            <div class="card-subtitle">
                                Notes: ${template.rating_min}-${template.rating_max} étoiles
                                ${template.is_active ? '• Actif' : '• Inactif'}
                            </div>
                        </div>
                    </div>
                    <div style="margin: 1rem 0; padding: 1rem; background: var(--bg-tertiary); border-radius: var(--radius);">
                        <pre style="white-space: pre-wrap; color: var(--text-secondary); font-size: 0.9rem;">${this.escapeHtml(template.content)}</pre>
                    </div>
                    <div class="review-actions">
                        <button class="btn btn-primary btn-sm" onclick="app.editTemplate(${template.id})">
                            ✏️ Modifier
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="app.deleteTemplate(${template.id})">
                            🗑️ Supprimer
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = `<div class="empty-state">Erreur: ${error.message}</div>`;
        }
    },

    showTemplateModal(templateId = null) {
        const modal = document.getElementById('templateModal');
        const form = document.getElementById('templateForm');
        const title = document.getElementById('templateModalTitle');

        if (templateId) {
            const template = this.templates.find(t => t.id === templateId);
            if (template) {
                title.textContent = 'Modifier le template';
                document.getElementById('templateId').value = template.id;
                document.getElementById('templateName').value = template.name;
                document.getElementById('templateContent').value = template.content;
                document.getElementById('templateRatingMin').value = template.rating_min;
                document.getElementById('templateRatingMax').value = template.rating_max;
                document.getElementById('templateActive').checked = template.is_active;
            }
        } else {
            title.textContent = 'Nouveau template';
            form.reset();
            document.getElementById('templateId').value = '';
        }

        modal.classList.add('active');
    },

    closeTemplateModal() {
        document.getElementById('templateModal').classList.remove('active');
    },

    async saveTemplate(e) {
        e.preventDefault();
        const form = e.target;
        const templateId = document.getElementById('templateId').value;
        const data = {
            name: document.getElementById('templateName').value,
            content: document.getElementById('templateContent').value,
            rating_min: parseInt(document.getElementById('templateRatingMin').value),
            rating_max: parseInt(document.getElementById('templateRatingMax').value),
            is_active: document.getElementById('templateActive').checked
        };

        try {
            if (templateId) {
                await this.api.put(`/templates/${templateId}`, data);
                this.showToast('Template modifié', 'success');
            } else {
                await this.api.post('/templates', data);
                this.showToast('Template créé', 'success');
            }
            this.closeTemplateModal();
            this.loadTemplates();
        } catch (error) {
            this.showToast('Erreur lors de l\'enregistrement', 'error');
        }
    },

    editTemplate(templateId) {
        this.showTemplateModal(templateId);
    },

    async deleteTemplate(templateId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce template ?')) {
            return;
        }

        try {
            await this.api.delete(`/templates/${templateId}`);
            this.showToast('Template supprimé', 'success');
            this.loadTemplates();
        } catch (error) {
            this.showToast('Erreur lors de la suppression', 'error');
        }
    },

    // Pending Replies
    async loadPendingReplies() {
        const container = document.getElementById('pendingList');
        container.innerHTML = '<div class="loading">Chargement...</div>';

        try {
            const pending = await this.api.get('/replies/pending');
            this.pendingReplies = pending;

            if (pending.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">✅</div>
                        <p>Aucune réponse en attente</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = pending.map(reply => `
                <div class="review-card">
                    <div class="review-header">
                        <div>
                            <div class="review-author">${this.escapeHtml(reply.review_author_name)}</div>
                            <div style="font-size: 0.9rem; color: var(--text-muted); margin-top: 0.25rem;">
                                ${this.escapeHtml(reply.location_name)} • ${new Date(reply.created_at).toLocaleDateString('fr-FR')}
                            </div>
                        </div>
                        <span class="rating-badge rating-${reply.review_rating}">${reply.review_rating}★</span>
                    </div>
                    ${reply.review_comment ? `<p class="review-comment">${this.escapeHtml(reply.review_comment)}</p>` : ''}
                    <div class="review-reply">
                        <strong>Suggestion de réponse:</strong>
                        <p>${this.escapeHtml(reply.suggested_reply)}</p>
                    </div>
                    <div class="review-actions">
                        <button class="btn btn-primary btn-sm" onclick="app.previewReply(${reply.id})">
                            👁️ Prévisualiser
                        </button>
                        <button class="btn btn-success btn-sm" onclick="app.approvePendingReply(${reply.id})">
                            ✅ Approuver
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="app.editPendingReply(${reply.id})">
                            ✏️ Modifier
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="app.rejectPendingReply(${reply.id})">
                            ❌ Rejeter
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = `<div class="empty-state">Erreur: ${error.message}</div>`;
        }
    },

    previewReply(pendingReplyId) {
        const reply = this.pendingReplies.find(r => r.id === pendingReplyId);
        if (!reply) return;

        this.currentPendingReplyId = pendingReplyId;
        document.getElementById('previewAuthorName').textContent = reply.review_author_name;
        document.getElementById('previewRating').textContent = `${reply.review_rating}★`;
        document.getElementById('previewRating').className = `rating-badge rating-${reply.review_rating}`;
        document.getElementById('previewComment').textContent = reply.review_comment || 'Aucun commentaire';
        document.getElementById('previewReplyText').value = reply.suggested_reply;

        document.getElementById('replyPreviewModal').classList.add('active');
    },

    closeReplyPreviewModal() {
        document.getElementById('replyPreviewModal').classList.remove('active');
        this.currentPendingReplyId = null;
    },

    async approvePendingReply(pendingReplyId = null) {
        const id = pendingReplyId || this.currentPendingReplyId;
        if (!id) return;

        const editedReply = document.getElementById('previewReplyText')?.value;
        const data = editedReply ? { edited_reply: editedReply } : {};

        try {
            this.showToast('Envoi de la réponse...', 'info');
            await this.api.post(`/replies/${id}/approve`, data);
            this.showToast('Réponse envoyée avec succès', 'success');
            this.closeReplyPreviewModal();
            this.loadPendingReplies();
            this.loadDashboard();
        } catch (error) {
            this.showToast('Erreur lors de l\'envoi', 'error');
        }
    },

    async editPendingReply(pendingReplyId) {
        const reply = this.pendingReplies.find(r => r.id === pendingReplyId);
        if (!reply) return;

        const newReply = prompt('Modifier la réponse:', reply.suggested_reply);
        if (!newReply) return;

        try {
            await this.api.post(`/replies/${pendingReplyId}/edit`, { suggested_reply: newReply });
            this.showToast('Réponse modifiée', 'success');
            this.loadPendingReplies();
        } catch (error) {
            this.showToast('Erreur lors de la modification', 'error');
        }
    },

    async rejectPendingReply(pendingReplyId) {
        if (!confirm('Êtes-vous sûr de vouloir rejeter cette suggestion ?')) {
            return;
        }

        try {
            await this.api.post(`/replies/${pendingReplyId}/reject`, {});
            this.showToast('Suggestion rejetée', 'success');
            this.loadPendingReplies();
        } catch (error) {
            this.showToast('Erreur lors du rejet', 'error');
        }
    },

    // Toast Notifications
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // Utility
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    app.init();

    // Setup template form
    const templateForm = document.getElementById('templateForm');
    if (templateForm) {
        templateForm.addEventListener('submit', (e) => app.saveTemplate(e));
    }

    // Setup filter listeners
    const ratingFilter = document.getElementById('reviewRatingFilter');
    const replyFilter = document.getElementById('reviewReplyFilter');
    if (ratingFilter) {
        ratingFilter.addEventListener('change', () => app.filterReviews());
    }
    if (replyFilter) {
        replyFilter.addEventListener('change', () => app.filterReviews());
    }
});


