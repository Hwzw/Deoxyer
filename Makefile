.PHONY: dev db-up db-down db-migrate lint test

db-up:
	docker compose up -d

db-down:
	docker compose down

dev:
	cd backend && uvicorn app.main:app --reload --port 8000

db-migrate:
	cd backend && alembic upgrade head

lint:
	cd backend && ruff check . && ruff format --check .

test:
	cd backend && python -m pytest
