PYTHON ?= python3
VENV := .venv

build:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements.txt

run:
	$(VENV)/bin/python solve.py 1>&2
