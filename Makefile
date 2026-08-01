# Smart Care Shield - Project Makefile

.PHONY: help install dev build start test lint format clean docker-up docker-down prisma-generate prisma-migrate prisma-studio

# Default target
.DEFAULT_GOAL := help

# ==========================================
# Help
# ==========================================
help: ## Show this help message
	@echo "Smart Care Shield - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# Setup & Installation
# ==========================================
install: ## Install dependencies
	npm ci
	npm run prisma:generate

install-dev: ## Install dependencies (including dev)
	npm install
	npm run prisma:generate

# ==========================================
# Development
# ==========================================
dev: ## Start development server
	npm run dev

build: ## Build production application
	npm run build

start: ## Start production server
	npm start

# ==========================================
# Code Quality
# ==========================================
lint: ## Run ESLint
	npm run lint

lint-fix: ## Fix ESLint errors
	npm run lint:fix

format: ## Format code with Prettier
	npm run format

format-check: ## Check code formatting
	npm run format:check

type-check: ## Run TypeScript type checking
	npm run type-check

# ==========================================
# Testing
# ==========================================
test: ## Run tests
	npm test

test-watch: ## Run tests in watch mode
	npm run test:watch

test-coverage: ## Run tests with coverage
	npm run test:ci

# ==========================================
# Database (Prisma)
# ==========================================
prisma-generate: ## Generate Prisma Client
	npm run prisma:generate

prisma-migrate: ## Run database migrations
	npm run prisma:migrate

prisma-migrate-deploy: ## Deploy migrations to production
	npm run prisma:migrate:deploy

prisma-studio: ## Open Prisma Studio
	npm run prisma:studio

prisma-reset: ## Reset database
	npm run prisma:reset

db-push: ## Push schema to database
	npm run db:push

db-seed: ## Seed database
	npm run db:seed

# ==========================================
# Docker
# ==========================================
docker-build: ## Build Docker image
	docker build -t smart-care-app .

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-clean: ## Remove Docker containers and volumes
	docker-compose down -v

# ==========================================
# Cleanup
# ==========================================
clean: ## Clean build artifacts and dependencies
	rm -rf .next out dist build coverage node_modules .turbo

clean-cache: ## Clean Next.js cache
	rm -rf .next .turbo

# ==========================================
# CI/CD
# ==========================================
ci: lint type-check test-coverage ## Run CI checks

# ==========================================
# All-in-One Commands
# ==========================================
setup: install prisma-migrate ## Setup project (install + migrate)

reset: clean install prisma-reset ## Reset and reinstall everything
