.PHONY: help setup backend frontend dev datahub-token seed seed-pinecone seed-langfuse seed-datahub status test lint typecheck check

BACKEND_PY := backend/.venv/bin/python
INGEST_PY := ingestion/.venv/bin/python

help: ## Show the available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend, ingestion and frontend dependencies, create .env
	test -d backend/.venv || python3 -m venv backend/.venv
	$(BACKEND_PY) -m pip install -q -r backend/requirements.txt
	test -d ingestion/.venv || python3 -m venv ingestion/.venv
	$(INGEST_PY) -m pip install -q -r ingestion/requirements.txt
	cd frontend && npm install --no-fund --no-audit
	test -f .env || cp .env.example .env

backend: ## API on http://localhost:8300 (Swagger at /docs)
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8300 --reload

frontend: ## App on http://localhost:3300
	cd frontend && npm run dev

dev: ## Backend and frontend together (Ctrl+C stops both)
	@trap 'kill 0' INT TERM EXIT; $(MAKE) backend & $(MAKE) frontend & wait

datahub-token: ## Create and save a DataHub token with the default datahub/datahub login
	cd backend && .venv/bin/python -m app.cli datahub-token

seed: ## Seed everything: Pinecone, Langfuse, then DataHub
	cd backend && .venv/bin/python -m app.cli seed all

seed-pinecone: ## Seed the Pinecone knowledge base
	cd backend && .venv/bin/python -m app.cli seed pinecone

seed-langfuse: ## Seed Langfuse prompts and a week of traffic
	cd backend && .venv/bin/python -m app.cli seed langfuse

seed-datahub: ## Ingest Pinecone and Langfuse into DataHub, add sources and lineage
	cd backend && .venv/bin/python -m app.cli seed datahub

status: ## Show connection and seed status
	cd backend && .venv/bin/python -m app.cli status

test: ## Backend tests
	cd backend && .venv/bin/python -m pytest -q

lint: ## Python lint and format check
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .

typecheck: ## Frontend type check and production build
	cd frontend && npm run build

check: test lint typecheck ## Everything CI runs
