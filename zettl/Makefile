BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

.PHONY: help up up-build down tag restore test e2e rebuild

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Stack ────────────────────────────────────────────────────────────────────

up: ## Start stack with existing images (no rebuild)
	docker-compose up

up-build: ## Rebuild all images and start stack
	docker-compose up --build

down: ## Stop and remove containers
	docker-compose down

# ── Image preservation ───────────────────────────────────────────────────────

tag: ## Tag current images with the current branch name (e.g. :skill-content)
	docker tag zettl-api:latest zettl-api:$(BRANCH)
	docker tag zettl-ui:latest zettl-ui:$(BRANCH)
	@echo "✓ Tagged images as :$(BRANCH)"

restore: ## Restore images from branch tag back to :latest (usage: make restore BRANCH=skill-content)
	docker tag zettl-api:$(BRANCH) zettl-api:latest
	docker tag zettl-ui:$(BRANCH) zettl-ui:latest
	@echo "✓ Restored images from :$(BRANCH)"

# ── Testing ──────────────────────────────────────────────────────────────────

test: ## Run API unit + integration tests
	cd api && pytest

e2e: ## Run E2E tests against running stack (stack must be up)
	cd ui && npx playwright test

# ── Safe rebuild workflow ────────────────────────────────────────────────────

rebuild: tag up-build ## Tag current branch, then rebuild (safe rebuild)
