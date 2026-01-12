# Variables d'environnement

Ce fichier documente toutes les variables d'environnement nécessaires pour le projet.

## Fichier .env

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```bash
# Backend Configuration
DATABASE_URL=sqlite:///./reviews.db
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Frontend Configuration
API_URL=http://localhost:8000

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost

# Google OAuth Configuration (REQUIS pour l'authentification)
GOOGLE_CLIENT_ID=votre_client_id_google
GOOGLE_CLIENT_SECRET=votre_client_secret_google
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
```

## Description des variables

### Backend

- **DATABASE_URL** : URL de connexion à la base de données SQLite
- **ENVIRONMENT** : Environnement d'exécution (`development` ou `production`)
- **DEBUG** : Active le mode debug (`True` ou `False`)
- **HOST** : Adresse IP d'écoute du serveur
- **PORT** : Port d'écoute du serveur

### Frontend

- **API_URL** : URL de l'API backend (utilisée par le frontend)

### CORS

- **CORS_ORIGINS** : Liste des origines autorisées pour CORS (séparées par des virgules)

### Google OAuth (Requis)

- **GOOGLE_CLIENT_ID** : ID client OAuth 2.0 obtenu depuis Google Cloud Console
- **GOOGLE_CLIENT_SECRET** : Secret client OAuth 2.0 obtenu depuis Google Cloud Console
- **GOOGLE_REDIRECT_URI** : URI de redirection après authentification OAuth

## Configuration Google Cloud Console

Pour obtenir les identifiants OAuth :

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'API "Google My Business API"
4. Allez dans "Identifiants" > "Créer des identifiants" > "ID client OAuth 2.0"
5. Configurez l'écran de consentement OAuth
6. Ajoutez `http://localhost:8000/auth/callback` dans les URI de redirection autorisés
7. Copiez le `Client ID` et le `Client Secret` dans votre fichier `.env`


