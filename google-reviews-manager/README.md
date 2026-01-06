# Google Reviews Manager

Gestionnaire d'avis Google - Outil d'assistance pour la gestion des avis (pas un bot automatique).

## 🏗️ Structure du projet

```
google-reviews-manager/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models/
│   │   └── schemas/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose installés
- Python 3.11+ (pour développement local)

### Avec Docker Compose (recommandé)

1. Clonez le projet et naviguez dans le dossier :
```bash
cd google-reviews-manager
```

2. Copiez le fichier d'environnement :
```bash
cp .env.example .env
```

3. Lancez les services :
```bash
docker-compose up -d
```

4. Accédez à l'application :
   - Frontend : http://localhost:8080
   - Backend API : http://localhost:8000
   - Health check : http://localhost:8000/health

### Développement local

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

Ouvrez simplement `frontend/index.html` dans votre navigateur, ou utilisez un serveur HTTP simple :

```bash
cd frontend
python -m http.server 8080
```

## 📋 Endpoints API

### Health Check
- **GET** `/health` - Retourne `{"status": "ok"}`

### Root
- **GET** `/` - Informations sur l'API

### Authentication (OAuth Google)
- **GET** `/auth/login` - Redirige vers la page d'autorisation Google OAuth
- **GET** `/auth/callback?code=...` - Callback OAuth, reçoit le code et stocke les tokens
- **GET** `/auth/accounts` - Liste tous les comptes Google connectés
- **DELETE** `/auth/accounts/{id}` - Déconnecte un compte Google

## 🛠️ Technologies

- **Backend** : FastAPI (Python 3.11+)
- **Frontend** : HTML5, CSS3, JavaScript vanilla
- **Base de données** : SQLite
- **Containerisation** : Docker & Docker Compose

## 📝 Notes

- Compatible Windows et Linux
- Base de données SQLite pour la simplicité et la portabilité
- Frontend simple sans framework lourd pour une maintenance facile

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à partir de `.env.example` et configurez les variables suivantes :

#### Backend
- `DATABASE_URL` : URL de la base de données (par défaut: `sqlite:///./reviews.db`)
- `HOST` : Adresse d'écoute du serveur (par défaut: `0.0.0.0`)
- `PORT` : Port du serveur (par défaut: `8000`)
- `ENVIRONMENT` : Environnement (development/production)
- `DEBUG` : Mode debug (True/False)

#### Google OAuth (requis pour l'authentification)
- `GOOGLE_CLIENT_ID` : ID client OAuth Google (obtenu depuis Google Cloud Console)
- `GOOGLE_CLIENT_SECRET` : Secret client OAuth Google
- `GOOGLE_REDIRECT_URI` : URI de redirection OAuth (par défaut: `http://localhost:8000/auth/callback`)

### Configuration Google Cloud Console

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'API "Google My Business API"
4. Allez dans "Identifiants" > "Créer des identifiants" > "ID client OAuth 2.0"
5. Configurez l'écran de consentement OAuth
6. Ajoutez `http://localhost:8000/auth/callback` dans les URI de redirection autorisés
7. Copiez le `Client ID` et le `Client Secret` dans votre fichier `.env`

### Scope OAuth utilisé
- `https://www.googleapis.com/auth/business.manage` : Gestion des profils Google Business
