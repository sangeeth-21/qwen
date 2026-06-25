.PHONY: install run clean build build-dmg

VENV ?= .venv
PYTHON ?= python3.12

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip setuptools wheel
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install py2app

run:
	$(VENV)/bin/python -m app

clean:
	rm -rf build dist *.egg-info $(VENV)

build:
	$(VENV)/bin/python setup.py py2app

build-dmg: build
	scripts/build_dmg.sh
