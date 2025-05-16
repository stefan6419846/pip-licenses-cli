REPO_NAME:=$(shell basename -s .git `git remote get-url origin`)
VENV_NAME:='venv/$(REPO_NAME)'
DEV_DEPENDS:='requirements/dev'

.DEFAULT_GOAL:= help
.PHONY: help
help:
	@echo 'Usage: make <subcommand>'
	@echo ''
	@echo 'Subcommands:'
	@echo '    setup           Setup for development'
	@echo '    local-install   Install locally'
	@echo '    local-uninstall Uninstall locally'
	@echo '    update-depends  Re-compile requirements for development'
	@echo '    lint            Re-lint by black and isort with setup.cfg'
	@echo '    test            Run unittests'
	@echo '    deploy          Release to PyPI server'
	@echo '    test-deploy     Release to Test PyPI server'
	@echo '    build           Build package'
	@echo '    clean           Clean directories'

.PHONY: setup
setup:
	test -d $(VENV_NAME) || python -m venv $(VENV_NAME)
	$(VENV_NAME)/bin/python -m pip install -r $(DEV_DEPENDS).txt

.PHONY: local-install
local-install:
	$(VENV_NAME)/bin/python -m pip install -e .

.PHONY: local-uninstall
local-uninstall:
	$(VENV_NAME)/bin/python -m pip uninstall -y pip-licenses

.PHONY: update-depends
update-depends:
	$(VENV_NAME)/bin/python -m pip-compile --extra dev -o requirements/dev.txt -U pyproject.toml

.PHONY: lint
lint:
	$(VENV_NAME)/bin/python -m black .
	$(VENV_NAME)/bin/python -m isort .
	$(VENV_NAME)/bin/python -m mypy --install-types --non-interactive .

.PHONY: test
test:
	$(VENV_NAME)/bin/python -m pytest

.PHONY: deploy
deploy: build
	$(VENV_NAME)/bin/python -m twine upload dist/*

.PHONY: test-deploy
test-deploy: build
	$(VENV_NAME)/bin/python -m twine upload -r pypitest dist/*

.PHONY: build
build: clean
	$(VENV_NAME)/bin/python -m build

.PHONY: clean
clean:
	rm -rf dist
