# Google Reviews Manager

Gestionnaire d'avis Google - Outil d'assistance pour la gestion des avis (pas un bot automatique).

## 📋 Table des matières

- [Présentation](#présentation)
- [Prérequis](#prérequis)
- [Installation rapide](#installation-rapide)
- [Configuration Google OAuth](#configuration-google-oauth)
- [Démarrage](#démarrage)
- [Utilisation](#utilisation)
- [Architecture](#architecture)
- [Documentation API](#documentation-api)
- [Dépannage](#dépannage)

## 🎯 Présentation

Google Reviews Manager est un outil d'assistance complet pour gérer les avis Google Business Profile. Il permet de :

- ✅ Connecter plusieurs comptes Google Business Profile
- ✅ Synchroniser automatiquement les établissements et avis
- ✅ Générer des réponses personnalisées avec des templates
- ✅ Valider manuellement les réponses avant envoi
- ✅ Suivre les réponses en attente de validation
- ✅ Filtrer et rechercher les avis facilement

## 📦 Prérequis

### Logiciels requis

- **Docker** (version 20.10+) et **Docker Compose** (version 2.0+)
  - [Installation Docker Desktop](https://docs.docker.com/get-docker/)
  - [Installation Docker Compose](https://docs.docker.com/compose/install/)

### Compte Google Cloud

- Un compte Google avec accès à Google Cloud Console
- Un projet Google Cloud (gratuit)
- Accès à Google Business Profile

## 🚀 Installation rapide

### 1. Cloner le projet

```bash
git clone <repository-url>
cd google-reviews-manager
```

### 2. Configurer les variables d'environnement

Copiez le fichier d'exemple et configurez-le :

```bash
cp .env.example .env
```

Éditez le fichier `.env` et configurez au minimum :

```env
GOOGLE_CLIENT_ID=votre_client_id
GOOGLE_CLIENT_SECRET=votre_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback
```

> ⚠️ **Important** : Vous devez d'abord créer les identifiants OAuth dans Google Cloud Console (voir section suivante).

### 3. Démarrer l'application

#### Linux/Mac

```bash
./scripts/start.sh
```

#### Windows

```cmd
scripts\start.bat
```

#### Ou manuellement avec Docker Compose

```bash
docker-compose up -d --build
```

### 4. Accéder à l'application

- **Frontend** : http://localhost:8080
- **Backend API** : http://localhost:8000
- **Health Check** : http://localhost:8000/health

## 🔐 Configuration Google OAuth

### Étape 1 : Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Cliquez sur le sélecteur de projet en haut
3. Cliquez sur **"Nouveau projet"**
4. Entrez un nom (ex: "Google Reviews Manager")
5. Cliquez sur **"Créer"**

### Étape 2 : Activer les APIs nécessaires

1. Dans le menu latéral, allez dans **"APIs & Services" > "Library"**
2. Recherchez et activez les APIs suivantes :
   - **Google My Business API**
   - **Google My Business Account Management API**
   - **Google My Business Business Information API**

### Étape 3 : Configurer l'écran de consentement OAuth

1. Allez dans **"APIs & Services" > "OAuth consent screen"**
2. Choisissez **"External"** (ou "Internal" si vous avez un compte Google Workspace)
3. Remplissez les informations :
   - **App name** : Google Reviews Manager
   - **User support email** : Votre email
   - **Developer contact information** : Votre email
4. Cliquez sur **"Save and Continue"**
5. Sur la page "Scopes", cliquez sur **"Add or Remove Scopes"**
6. Recherchez et ajoutez : `https://www.googleapis.com/auth/business.manage`
7. Cliquez sur **"Save and Continue"**
8. Ajoutez des utilisateurs de test si nécessaire
9. Cliquez sur **"Save and Continue"** puis **"Back to Dashboard"**

### Étape 4 : Créer les identifiants OAuth

1. Allez dans **"APIs & Services" > "Credentials"**
2. Cliquez sur **"+ CREATE CREDENTIALS" > "OAuth client ID"**
3. Choisissez **"Web application"**
4. Configurez :
   - **Name** : Google Reviews Manager Client
   - **Authorized JavaScript origins** :
     - `http://localhost:8080`
     - `http://localhost:3000` (si vous testez en développement)
   - **Authorized redirect URIs** :
     - `http://localhost:8080/auth/callback`
     - `http://localhost:8000/auth/callback` (pour développement direct)
5. Cliquez sur **"Create"**
6. **Copiez le Client ID et le Client Secret**
7. Collez-les dans votre fichier `.env` :

```env
GOOGLE_CLIENT_ID=votre_client_id_ici
GOOGLE_CLIENT_SECRET=votre_client_secret_ici
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback
```

### Étape 5 : Tester la connexion

1. Démarrez l'application
2. Allez sur http://localhost:8080
3. Cliquez sur **"Connecter un compte Google"**
4. Autorisez l'application
5. Vous devriez être redirigé et voir votre compte connecté

## 📖 Utilisation

### Interface principale

L'interface est divisée en plusieurs sections accessibles via le menu de navigation :

#### 🏠 Dashboard
- Vue d'ensemble avec statistiques
- Nombre de comptes, établissements, avis et réponses en attente
- Actions rapides

#### 👤 Comptes
- Liste des comptes Google connectés
- Bouton pour connecter un nouveau compte
- Déconnexion de comptes

#### 📍 Établissements
- Liste de tous les établissements
- Filtre par compte
- Synchronisation manuelle
- Accès direct aux avis d'un établissement

#### ⭐ Avis
- Liste complète des avis avec filtres :
  - Par établissement
  - Par note (1-5 étoiles)
  - Répondu / Non répondu
- Bouton pour suggérer une réponse

#### 📝 Templates
- Gestion des templates de réponses
- Création, modification, suppression
- Prévisualisation

#### ⏳ Réponses en attente
- File d'attente des réponses à valider
- Actions : Prévisualiser, Approuver, Modifier, Rejeter

### Workflow de réponse aux avis

1. **Synchroniser les avis** : Les avis sont automatiquement synchronisés depuis Google
2. **Générer une suggestion** : Cliquez sur "Suggérer une réponse" pour un avis
3. **Prévisualiser** : Vérifiez la réponse suggérée
4. **Modifier si nécessaire** : Éditez la réponse avant validation
5. **Approuver** : Validez et envoyez la réponse à Google
6. **Suivre** : La réponse apparaît sur Google Business Profile

## 🏗️ Architecture

### Structure du projet

```
google-reviews-manager/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application FastAPI
│   │   ├── config.py            # Configuration
│   │   ├── models/              # Modèles de base de données
│   │   ├── routers/             # Routes API
│   │   ├── services/            # Services métier
│   │   └── schemas/             # Schémas Pydantic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── nginx.conf               # Configuration Nginx
│   └── Dockerfile
├── scripts/
│   ├── start.sh                 # Script Linux/Mac
│   └── start.bat                # Script Windows
├── docker-compose.yml
├── .env.example
└── README.md
```

### Technologies

- **Backend** : FastAPI (Python 3.11+)
- **Frontend** : HTML5, CSS3, JavaScript vanilla (ES6+)
- **Base de données** : SQLite
- **Serveur web** : Nginx (frontend), Uvicorn (backend)
- **Containerisation** : Docker & Docker Compose

### Services Docker

- **backend** : Service FastAPI sur le port 8000 (interne)
- **frontend** : Service Nginx sur le port 80 (exposé sur 8080)
- **backend_data** : Volume persistant pour la base SQLite

## 📚 Documentation API

### Endpoints principaux

#### Authentication
- `GET /auth/login` - Redirige vers Google OAuth
- `GET /auth/callback` - Callback OAuth
- `GET /auth/accounts` - Liste des comptes
- `DELETE /auth/accounts/{id}` - Déconnecter un compte

#### Locations
- `GET /locations` - Liste des établissements
- `GET /locations/{id}` - Détails d'un établissement
- `POST /locations/{account_id}/sync` - Synchroniser les établissements

#### Reviews
- `GET /locations/{id}/reviews` - Liste des avis
- `POST /locations/{id}/reviews/sync` - Synchroniser les avis

#### Templates
- `GET /templates` - Liste des templates
- `POST /templates` - Créer un template
- `PUT /templates/{id}` - Modifier un template
- `DELETE /templates/{id}` - Supprimer un template
- `POST /templates/preview` - Prévisualiser un template

#### Replies
- `POST /replies/reviews/{id}/suggest-reply` - Suggérer une réponse
- `GET /replies/pending` - Liste des réponses en attente
- `POST /replies/{id}/approve` - Approuver et envoyer
- `POST /replies/{id}/reject` - Rejeter
- `POST /replies/{id}/edit` - Modifier

### Documentation interactive

Une fois l'application démarrée, accédez à :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🔧 Variables d'environnement

### Fichier .env

Créez un fichier `.env` à la racine du projet :

```env
# Backend Configuration
DATABASE_URL=sqlite:///./data/reviews.db
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Google OAuth (REQUIS)
GOOGLE_CLIENT_ID=votre_client_id_google
GOOGLE_CLIENT_SECRET=votre_client_secret_google
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:8080,http://localhost:3000

# Frontend Port (optionnel)
FRONTEND_PORT=8080
```

### Variables importantes

| Variable | Description | Requis |
|----------|-------------|--------|
| `GOOGLE_CLIENT_ID` | ID client OAuth Google | ✅ Oui |
| `GOOGLE_CLIENT_SECRET` | Secret client OAuth Google | ✅ Oui |
| `GOOGLE_REDIRECT_URI` | URI de redirection OAuth | ✅ Oui |
| `DATABASE_URL` | URL de la base de données | ❌ Non (défaut: SQLite) |
| `ENVIRONMENT` | Environnement (development/production) | ❌ Non |
| `DEBUG` | Mode debug | ❌ Non |

## 🐛 Dépannage

### Problèmes courants

#### L'application ne démarre pas

1. Vérifiez que Docker est installé et en cours d'exécution
2. Vérifiez que les ports 8000 et 8080 ne sont pas utilisés
3. Consultez les logs : `docker-compose logs`

#### Erreur OAuth "redirect_uri_mismatch"

1. Vérifiez que l'URI de redirection dans `.env` correspond exactement à celle configurée dans Google Cloud Console
2. L'URI doit être dans la liste "Authorized redirect URIs"
3. Redémarrez l'application après modification

#### Les avis ne se synchronisent pas

1. Vérifiez que les APIs Google sont activées dans Google Cloud Console
2. Vérifiez que le compte est bien connecté
3. Consultez les logs du backend : `docker-compose logs backend`

#### La base de données est perdue après redémarrage

1. Vérifiez que le volume Docker `backend_data` existe : `docker volume ls`
2. Le volume persiste les données même après suppression des conteneurs
3. Pour supprimer complètement : `docker-compose down -v` (⚠️ supprime les données)

### Commandes utiles

```bash
# Voir les logs
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend

# Redémarrer un service
docker-compose restart backend

# Arrêter l'application
docker-compose down

# Arrêter et supprimer les volumes (⚠️ supprime les données)
docker-compose down -v

# Reconstruire les images
docker-compose build --no-cache

# Voir l'état des services
docker-compose ps
```

## 📸 Captures d'écran

> 💡 **Note** : Les captures d'écran seront ajoutées dans une future version.

### Interface principale
![Dashboard](docs/screenshots/dashboard.png)

### Gestion des avis
![Reviews](docs/screenshots/reviews.png)

### Templates de réponses
![Templates](docs/screenshots/templates.png)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :

1. Consultez la section [Dépannage](#dépannage)
2. Vérifiez les [Issues](https://github.com/votre-repo/issues)
3. Créez une nouvelle issue si nécessaire

## 🎉 Remerciements

- Google pour l'API Google Business Profile
- FastAPI pour le framework backend
- Tous les contributeurs open source

---

**Fait avec ❤️ pour faciliter la gestion des avis Google**
