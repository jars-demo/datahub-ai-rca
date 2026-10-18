.PHONY: setup backend frontend dev test typecheck

PY := backend/.venv/bin/python

setup: ## Install backend and frontend dependencies
	test -d backend/.venv || python3 -m venv backend/.venv
	$(PY) -m pip install -q -r backend/requirements.txt
	cd frontend && npm install --no-fund --no-audit

backend: ## API on http://127.0.0.1:8000 (Swagger at /docs)
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend: ## UI on http://127.0.0.1:5173
	cd frontend && npm run dev

dev: ## Run backend and frontend together (Ctrl+C stops both)
	@trap 'kill 0' INT TERM EXIT; $(MAKE) backend & $(MAKE) frontend & wait

test: ## Backend tests
	cd backend && .venv/bin/python -m pytest -q

typecheck: ## Frontend type check
	cd frontend && npm run typecheck
