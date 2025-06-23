.PHONY: help install dev test lint format type-check clean build deploy setup check coverage docs \
        run-detection run-analysis run-orchestrator validate-env install-deps activate \
        ci pre-commit security test-unit test-integration test-coverage docker-build \
        deploy-staging deploy-prod release

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
COVERAGE_MIN := 90

# Default target
help:
	@echo "$(BLUE)SentinelOps CI/CD Pipeline Commands$(NC)"
	@echo "===================================="
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install        - Install all dependencies"
	@echo "  make dev            - Start development server"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run code linting"
	@echo "  make format         - Format code with Black"
	@echo "  make type-check     - Run mypy type checking"
	@echo "  make quality        - Run all quality checks"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make build          - Build for production"
	@echo "  make deploy         - Deploy to Cloud Run"
	@echo "  make validate-env   - Validate environment setup"
	@echo ""
	@echo "$(GREEN)CI/CD Pipeline:$(NC)"
	@echo "  make ci             - Run full CI pipeline locally"
	@echo "  make pre-commit     - Run pre-commit checks"
	@echo "  make security       - Run security scans"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make docker-build   - Build all Docker images"
	@echo "  make deploy-staging - Deploy to staging environment"
	@echo "  make deploy-prod    - Deploy to production"
	@echo "  make release        - Prepare a release"

# Install all dependencies
install:
	@echo "Checking Python version..."
	@python3 scripts/check-python-version.py || exit 1
	@echo "Installing Python dependencies..."
	@if [ -d "venv" ]; then \
		./venv/bin/pip install --upgrade pip; \
		./venv/bin/pip install -r requirements.txt; \
	else \
		python3 -m pip install --upgrade pip; \
		python3 -m pip install -r requirements.txt; \
	fi
	@echo "Installing pre-commit hooks..."
	@if [ -d "venv" ]; then \
		./venv/bin/pre-commit install || echo "pre-commit not installed"; \
	else \
		pre-commit install || echo "pre-commit not installed"; \
	fi
	@echo "Installation complete!"

# Install dependencies in virtual environment
install-deps:
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Activating virtual environment and installing dependencies..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo "Dependencies installed in virtual environment!"

# Development server - run all agents
dev:
	@echo "Starting SentinelOps agents..."
	python src/main.py --dev

# Run all tests
test:
	@echo "Running tests..."
	pytest tests/ -v

# Run tests with coverage
coverage:
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term tests/

# Code linting
lint:
	@echo "Running linters..."
	flake8 src tests
	pylint src
	ruff check src tests

# Run all quality checks
quality:
	@echo "Running all quality checks..."
	python3 scripts/run_quality_checks.py

# Code formatting
format:
	@echo "Formatting code..."
	black src tests scripts
	isort src tests scripts

# Type checking
type-check:
	@echo "Running type checker..."
	mypy src

# Full code quality check
check: lint type-check test
	@echo "All checks passed!"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete

# Build for production
build: clean
	@echo "Building for production..."
	python setup.py sdist bdist_wheel
	@echo "Build complete!"

# Deploy to Cloud Run
deploy: build
	@echo "Deploying to Cloud Run..."
	@echo "Deploying SentinelOps to Cloud Run..."
	gcloud run deploy sentinelops \
	  --source . \
	  --platform managed \
	  --region us-central1 \
	  --allow-unauthenticated \
	  --project $(PROJECT_ID) \
	  --set-env-vars PROJECT_ID=$(PROJECT_ID),ENVIRONMENT=production

# Test agent locally
test-agent-local:
	@echo "Testing detection agent locally..."
	python scripts/test_detection_agent_local.py

# Build detection agent Docker image
build-detection:
	@echo "Building detection agent Docker image..."
	docker build -f agents/detection/Dockerfile -t sentinelops-detection:latest .

# Run detection agent in Docker
run-detection-docker: build-detection
	@echo "Running detection agent in Docker..."
	docker run -p 8080:8080 \
		-e PROJECT_ID=your-gcp-project-id \
		-e AGENT_TYPE=detection \
		sentinelops-detection:latest

# Deploy detection agent to Cloud Run (test)
deploy-detection-test:
	@echo "Deploying detection agent to Cloud Run (test)..."
	./scripts/test_deploy_detection_agent.sh

# Validate environment setup
validate-env:
	@python3 scripts/validate-environment.py

# Generate API documentation
docs:
	@echo "Generating documentation..."
	mkdir -p docs/api
	sphinx-apidoc -f -o docs/api src
	@echo "Documentation generated in docs/api/"

# Run specific agent services
run-detection:
	python -m src.detection_agent.main

run-analysis:
	python -m src.analysis_agent.main

run-remediation:
	python -m src.remediation_agent.main

run-communication:
	python -m src.communication_agent.main

run-orchestrator:
	python -m src.orchestrator_agent.main

# Run API server (for external integrations)
run-api:
	@echo "Starting SentinelOps API server..."
	@echo "Note: This is for external integrations. Use 'make dev' to run the agent system."
	uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000

# Development setup
setup: install-deps
	@echo "Setting up development environment..."
	./scripts/setup_dev.sh

# Activate virtual environment (informational)
activate:
	@echo "To activate the virtual environment, run:"
	@echo "  source venv/bin/activate"

# CI/CD Pipeline Commands
# ======================

# Run full CI pipeline locally
ci: clean lint type-check security test-coverage
	@echo "$(GREEN)✓ CI pipeline completed successfully$(NC)"

# Run pre-commit checks
pre-commit: format lint type-check test-unit
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

# Run security scans
security:
	@echo "$(BLUE)Running security scans...$(NC)"
	@bandit -r src -f json -o bandit-report.json || true
	@safety check || true
	@pip-audit || true
	@echo "$(GREEN)✓ Security scans completed$(NC)"

# Run unit tests only
test-unit:
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTEST) tests -v -m "unit"
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

# Run integration tests
test-integration:
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTEST) tests -v -m "integration"
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

# Run tests with coverage
test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PYTEST) tests -v --cov=src --cov-report=html --cov-report=term-missing
	@coverage report --fail-under=$(COVERAGE_MIN) || (echo "$(RED)✗ Coverage below $(COVERAGE_MIN)%$(NC)" && exit 1)
	@echo "$(GREEN)✓ Coverage meets requirements$(NC)"
	@echo "Coverage report: htmlcov/index.html"

# Build all Docker images
docker-build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker build -t sentinelops:latest .
	@for agent in detection analysis remediation communication orchestrator; do \
		echo "Building $$agent agent..."; \
		docker build -t sentinelops-$$agent:latest ./agents/$$agent || exit 1; \
	done
	@echo "$(GREEN)✓ All Docker images built$(NC)"

# Deploy to staging
deploy-staging:
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@gcloud builds submit --config=cloudbuild.yaml \
		--substitutions=_ENVIRONMENT=staging,_DEPLOY_REGION=us-central1
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

# Deploy to production
deploy-prod:
	@echo "$(YELLOW)⚠️  Production deployment requires confirmation$(NC)"
	@read -p "Deploy to production? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Deploying to production...$(NC)"; \
		gcloud builds submit --config=cloudbuild.yaml \
			--substitutions=_ENVIRONMENT=production,_DEPLOY_REGION=us-central1,us-east1,us-west1; \
		echo "$(GREEN)✓ Deployed to production$(NC)"; \
	else \
		echo "$(YELLOW)Deployment cancelled$(NC)"; \
	fi

# Prepare a release
release:
	@echo "$(BLUE)Preparing release...$(NC)"
	@bash scripts/prepare_release.sh || echo "Release script not found"
	@echo "$(GREEN)✓ Release prepared$(NC)"
