.PHONY: help up down logs check backend-install backend-lint backend-fmt backend-test \
        frontend-install frontend-lint frontend-test migrate revision demo audit \
        production-config production-build production-up production-logs

help:
	@echo "AgentiCubed make targets:"
	@echo "  up               docker compose up --build"
	@echo "  down             docker compose down"
	@echo "  logs             tail compose logs"
	@echo "  check            backend + frontend lint and tests"
	@echo "  backend-install  install backend (editable, dev extras)"
	@echo "  backend-lint     ruff + black --check"
	@echo "  backend-fmt      black + ruff --fix"
	@echo "  backend-test     pytest"
	@echo "  frontend-install npm ci"
	@echo "  frontend-lint    eslint"
	@echo "  frontend-test    vitest run"
	@echo "  migrate          alembic upgrade head"
	@echo "  revision m=msg   alembic autogenerate revision"
	@echo "  demo             run the end-to-end demonstration project"
	@echo "  audit            dependency-audit gate (pip-audit + npm audit + waivers)"
	@echo "  production-config validate compose.production.yml with .env.production"
	@echo "  production-build  build production API + frontend images"
	@echo "  production-up     start the single-node production stack"
	@echo "  production-logs   tail production stack logs"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

check: backend-lint backend-test frontend-lint frontend-test

backend-install:
	cd backend && pip install -e ".[dev,analysis]"

demo:
	cd backend && python -m app.seed.demo

backend-lint:
	cd backend && ruff check . && black --check .

backend-fmt:
	cd backend && black . && ruff check --fix .

backend-test:
	cd backend && pytest

frontend-install:
	cd frontend && npm ci

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm run test

audit:
	python scripts/dependency_audit.py backend
	python scripts/dependency_audit.py frontend

production-config:
	docker compose --env-file .env.production -f compose.production.yml config -q

production-build:
	docker compose --env-file .env.production -f compose.production.yml build api frontend

production-up:
	docker compose --env-file .env.production -f compose.production.yml up -d

production-logs:
	docker compose --env-file .env.production -f compose.production.yml logs -f --tail=100

migrate:
	cd backend && alembic upgrade head

revision:
	cd backend && alembic revision --autogenerate -m "$(m)"
