@echo off
REM Script de démarrage pour Windows
REM Google Reviews Manager

echo.
echo ====================================
echo   Google Reviews Manager - Demarrage
echo ====================================
echo.

REM Vérifier que Docker est installé
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Docker n'est pas installe.
    echo          Veuillez installer Docker Desktop d'abord.
    echo          Visitez: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Vérifier que Docker Compose est disponible
docker compose version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker-compose version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] Docker Compose n'est pas installe.
        echo          Veuillez installer Docker Compose d'abord.
        echo          Visitez: https://docs.docker.com/compose/install/
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE=docker-compose
) else (
    set DOCKER_COMPOSE=docker compose
)

REM Vérifier que le fichier .env existe
if not exist .env (
    echo [ATTENTION] Le fichier .env n'existe pas.
    echo             Creation d'un fichier .env a partir de .env.example...
    if exist .env.example (
        copy .env.example .env >nul
        echo             [OK] Fichier .env cree. Veuillez le configurer avec vos identifiants Google OAuth.
        echo             Consultez le README.md pour les instructions detaillees.
        pause
        exit /b 1
    ) else (
        echo [ERREUR] Le fichier .env.example n'existe pas non plus.
        pause
        exit /b 1
    )
)

REM Aller à la racine du projet
cd /d "%~dp0\.."

echo [OK] Verifications terminees
echo.
echo Construction et demarrage des conteneurs...
echo.

REM Construire et démarrer les services
%DOCKER_COMPOSE% up -d --build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Services demarres avec succes!
    echo.
    echo Accedez a l'application:
    echo   Frontend: http://localhost:8080
    echo   Backend API: http://localhost:8000
    echo   Health Check: http://localhost:8000/health
    echo.
    echo Commandes utiles:
    echo   Voir les logs: %DOCKER_COMPOSE% logs -f
    echo   Arreter: %DOCKER_COMPOSE% down
    echo   Redemarrer: %DOCKER_COMPOSE% restart
    echo.
) else (
    echo.
    echo [ERREUR] Echec du demarrage des services.
    echo          Verifiez les logs avec: %DOCKER_COMPOSE% logs
    echo.
)

pause


