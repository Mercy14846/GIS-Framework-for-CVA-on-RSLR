.PHONY: setup test lint dev-api dev-web up
setup:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm ci
test:
	cd backend && . .venv/bin/activate && pytest -q
lint:
	cd backend && . .venv/bin/activate && ruff check src tests
dev-api:
	cd backend && . .venv/bin/activate && uvicorn coastal_dss.api.main:app --reload --port 8000
dev-web:
	cd frontend && npm run dev
up:
	docker compose up --build
