PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
MAIN ?= a_maze_ing.py
CONFIG ?= config.txt

.PHONY: install run debug clean lint lint-strict

install:
	$(PIP) install .
run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist *.egg_info
	find - -type f -name "*.py[co]" -delete

lint:
	flake8 . --exclude=.venv,venv,env,__pycache__,.git
	mypy . --explicit-package-bases --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude=.venv,venv,env,__pycache__,.git

lint-strict:
	flake8 . --exclude=.venv,venv,env,__pycache__,.git
	mypy . --explicit-package-bases --strict --exclude=.venv,venv,env,__pycache__,.git