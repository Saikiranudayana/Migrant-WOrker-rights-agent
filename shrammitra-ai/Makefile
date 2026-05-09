.PHONY: help dev build test lint clean ingest migrate

help:
	@echo "ShramMitra AI — Makefile Commands"
	@echo ""
	@echo "  make dev        Start local development environment"
	@echo "  make build      Build Docker images"
	@echo "  make test       Run full test suite"
	@echo "  make lint       Lint all code"
	@echo "  make ingest     Run knowledge base ingestion pipeline"
	@echo "  make migrate    Run database migrations"
	@echo "  make clean      Remove containers and volumes"
	@echo "  make logs       Tail Docker logs"
	@echo "  make shell      Open backend shell"

dev:
	docker compose up --build

build:
	docker compose build

test:
	cd backend && pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

test-unit:
	cd backend && pytest tests/unit/ -v

test-integration:
	cd backend && pytest tests/integration/ -v

test-security:
	cd backend && pytest tests/security/ -v

lint:
	cd backend && ruff check app/ tests/ && mypy app/
	cd frontend && npm run lint

ingest:
	cd ingestion && python sync_jobs/run_sync.py

migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

logs:
	docker compose logs -f

shell:
	docker compose exec backend bash

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

create-index:
	cd backend && python -c "from app.rag.index_manager import IndexManager; import asyncio; asyncio.run(IndexManager().create_index())"

reindex:
	curl -X POST http://localhost:8000/admin/reindex \
		-H "Authorization: Bearer $$(cat .admin-token)" \
		-H "Content-Type: application/json"

health:
	curl -s http://localhost:8000/health | python -m json.tool
