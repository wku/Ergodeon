# ergodeon Agent System - Makefile

.PHONY: help install dev-install test lint format clean docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Kirergodeono Agent System - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies with pip
	pip install -r requirements.txt

poetry-install: ## Install dependencies with Poetry
	poetry install

poetry-install-all: ## Install all dependencies including optional
	poetry install --extras all

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black ruff mypy isort pre-commit

# Development
run: ## Run the CLI
	python -m src.main

run-interactive: ## Run in interactive mode
	python -m src.main

test: ## Run tests
	pytest

test-verbose: ## Run tests with verbose output
	pytest -v

test-coverage: ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term-missing

# Code quality
lint: ## Run linters
	ruff check .
	mypy .

format: ## Format code
	black .
	isort .

format-check: ## Check code formatting
	black --check .
	isort --check .

# Docker
docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in Docker container
	docker-compose exec ergodeon /bin/bash

docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker system prune -f

# Docker with profiles
docker-up-api: ## Start with API
	docker-compose --profile api up -d

docker-up-ui: ## Start with UI
	docker-compose --profile ui up -d

docker-up-all: ## Start all services
	docker-compose --profile api --profile ui up -d

# Poetry specific
poetry-shell: ## Activate Poetry shell
	poetry shell

poetry-update: ## Update dependencies
	poetry update

poetry-export: ## Export requirements.txt
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Cleaning
clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

clean-data: ## Clean data directories
	rm -rf data/chroma/*
	rm -rf logs/*

# Setup
setup: ## Initial setup
	cp .env.example .env
	mkdir -p data/chroma logs
	@echo "Please edit .env file with your API keys"

setup-poetry: ## Setup with Poetry
	poetry install
	cp .env.example .env
	mkdir -p data/chroma logs
	@echo "Please edit .env file with your API keys"

# Pre-commit
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

# Documentation
docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not yet implemented"

# All-in-one commands
all: clean install test lint ## Clean, install, test, and lint

dev-setup: dev-install setup pre-commit-install ## Complete development setup

docker-rebuild: docker-down docker-build docker-up ## Rebuild and restart Docker
