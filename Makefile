# Makefile for Aegis project
# Provides convenient shortcuts for common tasks

.PHONY: help install test test-unit test-integration test-cov test-fast clean lint format setup-dev

help:
	@echo "Aegis Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies"
	@echo "  make setup-dev    Set up development environment"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-unit    Run unit tests only (fast)"
	@echo "  make test-integration  Run integration tests"
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make test-fast    Run fast tests (no API, no secrets)"
	@echo "  make test-smoke   Run smoke tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run linters (flake8, mypy)"
	@echo "  make format       Format code (black, isort)"
	@echo "  make check        Run format checks without modifying"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove generated files"
	@echo "  make clean-cache  Remove data cache"
	@echo ""
	@echo "Running:"
	@echo "  make daily-update Run daily update script"
	@echo "  make status       Show current risk status"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock pytest-timeout black isort flake8 mypy safety bandit

# Setup
setup-dev: install-dev
	@echo "Creating config directories..."
	@mkdir -p config/credentials data/cache/fred data/cache/yahoo data/history
	@if [ ! -f config/credentials/secrets.ini ]; then \
		echo "Copying secrets template..."; \
		cp config/credentials/secrets.ini.example config/credentials/secrets.ini; \
		echo ""; \
		echo "⚠️  Please edit config/credentials/secrets.ini and add your API keys"; \
	fi
	@echo "Development environment ready!"

# Testing
test:
	pytest

test-unit:
	pytest -m unit -v

test-integration:
	pytest -m integration -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/"
	@echo "Open htmlcov/index.html in your browser"

test-fast:
	pytest -m "not api and not requires_secrets and not slow" -v

test-smoke:
	pytest -m smoke -v

test-watch:
	pytest-watch

test-parallel:
	pytest -n auto

# Code Quality
lint:
	@echo "Running Flake8..."
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
	flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo ""
	@echo "Running MyPy..."
	mypy src/ --ignore-missing-imports --no-strict-optional || true

format:
	@echo "Running Black..."
	black src/ tests/
	@echo ""
	@echo "Running isort..."
	isort --profile black src/ tests/

check:
	@echo "Checking Black formatting..."
	black --check src/ tests/
	@echo ""
	@echo "Checking isort..."
	isort --check-only --profile black src/ tests/

security:
	@echo "Running Safety (dependency check)..."
	safety check || true
	@echo ""
	@echo "Running Bandit (security linting)..."
	bandit -r src/ || true

# Running scripts
daily-update:
	python scripts/daily_update.py

status:
	python scripts/show_status.py

weekly-report:
	python scripts/weekly_report.py

backtest:
	python scripts/backtest.py --start-date 2000-01-01

# Configuration
test-config:
	python src/config/config_manager.py --test

# Cleanup
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov coverage.xml coverage.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	@echo "Clean complete!"

clean-cache:
	@echo "Cleaning data cache..."
	rm -rf data/cache/fred/* data/cache/yahoo/*
	@echo "Cache cleared!"

clean-all: clean clean-cache
	@echo "All temporary files and caches removed!"

# CI/CD simulation
ci-lint: check lint

ci-test: test-fast

ci-full: ci-lint ci-test test-cov

# Docker (future)
docker-build:
	docker build -t aegis:latest .

docker-run:
	docker run -it aegis:latest

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "Not yet implemented"

# Git hooks
pre-commit: format lint test-fast
	@echo "✅ Pre-commit checks passed!"

# Coverage badge
coverage-badge:
	pip install coverage-badge
	coverage-badge -o coverage.svg -f

# Development server (if dashboard exists)
dashboard:
	python src/dashboard/app.py

# Version bump (requires bump2version)
bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major
