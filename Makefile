.PHONY: check format help install-dev lint run test

# ============================================================================
# VARIABLES
# ============================================================================

PYTHON := python3
PIP := pip
VENV := .venv
PROJECT_NAME := python_pubsub_scanner
PROJECT_PATH := src/python_pubsub_scanner
GH_PACKAGES_URL := https://pypi.pkg.github.com/venantvr-trading/

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "Makefile Commands:"
	@echo "  check          Run all checks (format, lint, and test)"
	@echo "  format         Format code with black"
	@echo "  install-dev    Install project in editable mode with dev dependencies"
	@echo "  lint           Run linting (flake8 + mypy)"
	@echo "  run            Run the scanner (example usage)"
	@echo "  test           Run tests with pytest"

# ============================================================================
# SETUP & INSTALLATION
# ============================================================================

install-dev:
	@if [ ! -d "$(VENV)" ]; then $(PYTHON) -m venv $(VENV); fi
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	@. $(VENV)/bin/activate && $(PIP) install --extra-index-url $(GH_PACKAGES_URL) -e ".[dev]"
	@echo "✅ Development environment ready! Activate with: source $(VENV)/bin/activate"

# ============================================================================
# QUALITY & TESTING
# ============================================================================

check: format lint test
	@echo "✅ All checks passed!"

format:
	@echo "✨ Formatting code..."
	@. $(VENV)/bin/activate && black $(PROJECT_PATH)
	@echo "✅ Formatting complete!"

lint:
	@echo "🔍 Running linting..."
	@. $(VENV)/bin/activate && flake8 $(PROJECT_PATH)
	@. $(VENV)/bin/activate && mypy $(PROJECT_PATH) --ignore-missing-imports
	@echo "✅ Linting complete!"

test:
	@echo "🧪 Running tests..."
	@. $(VENV)/bin/activate && pytest
	@echo "✅ Tests complete!"

# ============================================================================
# RUN
# ============================================================================

run:
	@. $(VENV)/bin/activate && pubsub-scanner --agents-dir /path/to/your/agents --api-url http://localhost:5555 --one-shot
	@echo "✅ Scan complete!"
