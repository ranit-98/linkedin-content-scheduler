.PHONY: install lint test migrate run worker scheduler up down

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

test:
	pytest --cov=app --cov-report=term-missing

migrate:
	alembic upgrade head

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.workers.celery_app:celery_app worker -Q linkedin-publishing --loglevel=INFO

scheduler:
	celery -A app.workers.celery_app:celery_app beat --loglevel=INFO

up:
	docker compose up --build

down:
	docker compose down

