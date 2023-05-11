.PHONY: help bootstrap lint test requirements

VENV?=.venv
PYTHON?=python3

help:
	@echo
	@echo "make install         -- setup production environment"
	@echo
	@echo "make development     -- setup development environment"
	@echo "make test            -- run full test suite"
	@echo "make lint            -- run all linters on the code base"
	@echo
	@echo "make requirements    -- only compile the requirements*.txt files"
	@echo "make .venv           -- bootstrap the virtualenv."
	@echo

install: $(VENV)/.pip-installed-production

development: $(VENV)/.pip-installed-development .git/hooks/pre-commit
	$(VENV)/bin/pip install -e .

lint: development
	$(VENV)/bin/python -c "import sys; print(sys.path); import os; print(os.environ)"
	$(VENV)/bin/pre-commit run -a

test: development
	$(VENV)/bin/pytest

requirements: requirements.txt requirements-dev.txt

requirements.txt: pyproject.toml
	$(VENV)/bin/pip-compile -v --resolver=backtracking --output-file=$@ $<

requirements-dev.txt: pyproject.toml
	$(VENV)/bin/pip-compile -v --resolver=backtracking --output-file=$@ --extra=dev $<

# Actual files/directories
################################################################################

# Create this directory as a symbolic link to an existing virtualenv, if you want to use that.
$(VENV):
	$(PYTHON) -m venv --system-site-packages $(VENV)
	$(VENV)/bin/pip install pip-tools wheel
	touch $(VENV)

$(VENV)/.pip-installed-production: $(VENV) requirements.txt
	$(VENV)/bin/pip-sync requirements.txt && touch $@

$(VENV)/.pip-installed-development: $(VENV) requirements-dev.txt
	$(VENV)/bin/pip-sync requirements-dev.txt && touch $@

.git/hooks/pre-commit: $(VENV)
	$(VENV)/bin/pre-commit install
	touch .git/hooks/pre-commit
