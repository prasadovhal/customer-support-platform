.DEFAULT_GOAL := help

.PHONY: help dev-up dev-down migrate seed init-db test test-unit test-integration lint format shell logs

help:
	@echo "Available targets:"
	@echo "  dev-up            Start db and redis services"
	@echo "  dev-down          Stop all services"
	@echo "  migrate           Run Alembic migrations"
	@echo "  seed              Seed the database from CSV files"
	@echo "  init-db           Run migrations then seed the database"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests"
	@echo "  test-integration  Run integration tests"
	@echo "  lint              Lint source with ruff"
	@echo "  format            Format source with black"
	@echo "  shell             Open a shell in the api container"
	@echo "  logs              Tail logs for api and worker"

dev-up:
	docker compose up -d db redis

dev-down:
	docker compose down

migrate:
	alembic upgrade head

seed:
	python scripts/seed_db.py

init-db:
	python scripts/init_db.py

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

lint:
	ruff check src/ tests/

format:
	black src/ tests/

shell:
	docker compose exec api bash

logs:
	docker compose logs -f api worker
