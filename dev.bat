@echo off
REM Curestry Development Commands for Windows

if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="logs" goto logs
if "%1"=="build" goto build
if "%1"=="clean" goto clean
if "%1"=="health" goto health
if "%1"=="ps" goto ps
if "%1"=="help" goto help
if "%1"=="" goto help

:help
echo Curestry Development Commands:
echo.
echo   dev up         - Start all services
echo   dev down       - Stop all services
echo   dev logs       - View all service logs
echo   dev build      - Build Docker images
echo   dev clean      - Clean up Docker resources
echo   dev health     - Check service health
echo   dev ps         - View running containers
echo   dev help       - Show this help message
echo.
echo Note: Make sure Docker Desktop is running before using these commands
goto end

:up
echo Starting Curestry services...
cd infra
docker compose up -d
if %errorlevel%==0 (
    echo Services started. API: http://localhost:8000, Web: http://localhost:3000
) else (
    echo Failed to start services. Make sure Docker Desktop is running.
)
cd ..
goto end

:down
echo Stopping Curestry services...
cd infra
docker compose down
cd ..
goto end

:logs
cd infra
docker compose logs -f
cd ..
goto end

:build
echo Building Docker images...
cd infra
docker compose build
cd ..
goto end

:clean
echo Cleaning up Docker resources...
cd infra
docker compose down -v
cd ..
docker system prune -f
goto end

:health
echo Checking service health...
curl -f http://localhost:8000/healthz || echo API health check failed
curl -f http://localhost:3000 || echo Web health check failed
goto end

:ps
cd infra
docker compose ps
cd ..
goto end

:end