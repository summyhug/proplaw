.PHONY: install lint test run setup-dev frontend-install frontend-lint frontend-build

install:
	pip install -r requirements.txt

lint:
	ruff check .

test:
	pytest

run:
	uvicorn propra.main:app --reload

setup-dev:
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

frontend-install:
	cd propra/frontend && npm install

frontend-lint:
	cd propra/frontend && npm run lint

frontend-build:
	cd propra/frontend && npm run build
