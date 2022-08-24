.PHONY: all
all: lint lint.deep test

.PHONY: lint
lint: isort black flake8 bandit safety mypy

.PHONY: lint.deep
lint.deep:  ## complex analise
	poetry run pylint ipl_config/ tests/

.PHONY: mypy
mypy:  ## static type check
	poetry run mypy .

.PHONY: flake8
flake8:  ## pyflakes + pep8
	poetry run flake8 .

.PHONY: bandit
bandit:  ## find common security issues
	poetry run bandit --ini .bandit -r .

.PHONY: safety
safety: ## checks your installed dependencies for known security vulnerabilities
	poetry run safety check

.PHONY: test
test:
	poetry run pytest tests/ --cov=ipl_config

.PHONY: black
black:
	poetry run black -S -l 79 --diff --check ipl_config/ tests/

.PHONY: isort
isort:
	poetry run isort --check-only --diff ipl_config/ tests/
