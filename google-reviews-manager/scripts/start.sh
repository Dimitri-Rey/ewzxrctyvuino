#!/bin/bash

# Script de démarrage pour Linux/Mac
# Google Reviews Manager

set -e

echo "🚀 Google Reviews Manager - Démarrage"
echo "======================================"
echo ""

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker d'abord."
    echo "   Visitez: https://docs.docker.com/get-docker/"
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord."
    echo "   Visitez: https://docs.docker.com/compose/install/"
    exit 1
fi

# Vérifier que le fichier .env existe
if [ ! -f .env ]; then
    echo "⚠️  Le fichier .env n'existe pas."
    echo "   Création d'un fichier .env à partir de .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "   ✅ Fichier .env créé. Veuillez le configurer avec vos identifiants Google OAuth."
        echo "   📝 Consultez le README.md pour les instructions détaillées."
        exit 1
    else
        echo "   ❌ Le fichier .env.example n'existe pas non plus."
        exit 1
    fi
fi

# Vérifier que GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET sont définis
source .env 2>/dev/null || true
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "⚠️  GOOGLE_CLIENT_ID ou GOOGLE_CLIENT_SECRET ne sont pas définis dans .env"
    echo "   Veuillez configurer ces variables avant de continuer."
    echo "   📝 Consultez le README.md pour les instructions détaillées."
    exit 1
fi

# Aller à la racine du projet
cd "$(dirname "$0")/.." || exit 1

echo "✅ Vérifications terminées"
echo ""
echo "🔨 Construction et démarrage des conteneurs..."
echo ""

# Utiliser docker compose ou docker-compose selon ce qui est disponible
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Construire et démarrer les services
$DOCKER_COMPOSE up -d --build

echo ""
echo "✅ Services démarrés avec succès!"
echo ""
echo "📊 Accédez à l'application:"
echo "   Frontend: http://localhost:${FRONTEND_PORT:-8080}"
echo "   Backend API: http://localhost:8000"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "📝 Commandes utiles:"
echo "   Voir les logs: $DOCKER_COMPOSE logs -f"
echo "   Arrêter: $DOCKER_COMPOSE down"
echo "   Redémarrer: $DOCKER_COMPOSE restart"
echo ""
