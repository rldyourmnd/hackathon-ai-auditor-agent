# Curestry Development Makefile
# Cross-platform commands for development workflow

.PHONY: help up down logs build clean health ps lint test format install-dev

# Default target
help: ## Show this help message
	@echo "Curestry Development Commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Note: Make sure Docker Desktop is running before using these commands"

# Docker operations
up: ## Start all services
	@echo "Starting Curestry services..."
	cd infra && docker compose up -d
	@echo "Services started. API: http://localhost:8000, Web: http://localhost:3000"

down: ## Stop all services
	@echo "Stopping Curestry services..."
	cd infra && docker compose down

logs: ## View all service logs
	cd infra && docker compose logs -f

build: ## Build Docker images
	@echo "Building Docker images..."
	cd infra && docker compose build

clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	cd infra && docker compose down -v
	docker system prune -f

health: ## Check service health
	@echo "Checking service health..."
	@curl -f http://localhost:8000/healthz || echo "API health check failed"
	@curl -f http://localhost:3000 || echo "Web health check failed"

ps: ## View running containers
	cd infra && docker compose ps

# Development tools
lint: ## Run linters on all code
	@echo "Running backend linting..."
	cd backend && python -m ruff check . --fix
	cd backend && python -m ruff format .
	cd backend && python -m isort .
	@echo "Running frontend linting..."
	cd frontend && npm run lint:fix
	cd frontend && npm run format

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

format: ## Format all code
	@echo "Formatting backend code..."
	cd backend && python -m ruff format .
	cd backend && python -m isort .
	@echo "Formatting frontend code..."
	cd frontend && npm run format

install-dev: ## Install development dependencies
	@echo "Installing Python development tools..."
	pip install ruff black isort mypy pytest pre-commit
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing pre-commit hooks..."
	pre-commit install
