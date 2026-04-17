.PHONY: help setup up down rebuild logs smoke demo

ENV_FILE ?= stack.env

help:
	@echo "Targets:"
	@echo "  make setup    - create stack.env from template if missing"
	@echo "  make up       - start Idun Agent Engine with Docker Compose"
	@echo "  make down     - stop compose stack"
	@echo "  make rebuild  - rebuild idun-agent image without cache"
	@echo "  make logs     - tail stack logs"
	@echo "  make smoke    - run smoke checks"
	@echo "  make demo     - send a sample /agent/run request"

setup:
	@test -f "$(ENV_FILE)" || cp stack.env.example "$(ENV_FILE)"
	@echo "Using env file: $(ENV_FILE)"
	@echo "Set COMPRESS_API_KEY in $(ENV_FILE) before running 'make up' (LightReach key: lr_…)"

up:
	docker compose --env-file "$(ENV_FILE)" up --build

down:
	docker compose --env-file "$(ENV_FILE)" down

rebuild:
	docker compose --env-file "$(ENV_FILE)" build --no-cache idun-agent

logs:
	docker compose --env-file "$(ENV_FILE)" logs -f

smoke:
	bash scripts/smoke_test.sh

demo:
	bash scripts/demo_request.sh
