# based on remote (requires remote named origin)
# REPO_NAME:=$(shell basename -s .git `git remote get-url origin`)
# get the local clone directory name (always will exist in clones, even if you call your remote fork on github "github" and setup the remote "upstream")
REPO_NAME:=$(shell basename `git rev-parse --show-toplevel`)
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

venv:
	test -d $@ || mkdir -m 755 ./$@

$(VENV_NAME): venv
	test -d $(VENV_NAME) || python -m venv $(VENV_NAME)
	test -d $(VENV_NAME) || exit 1 ;

.PHONY: setup
setup: $(VENV_NAME)
	$(VENV_NAME)/bin/python -m pip install -r $(DEV_DEPENDS).txt

.PHONY: local-install
local-install: $(VENV_NAME)
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
	$(VENV_NAME)/bin/python -m flake8 .
	$(VENV_NAME)/bin/python -m mypy .

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

.PHONY: full-clean
full-clean:: local-uninstall clean
	rm -vrf *.egg-info 2>/dev/null || : ;
	rm -vfrd ./{piplicenses,tests}/__pycache__ 2>/dev/null || : ;
	rm -vfrd ./.coverage 2>/dev/null || : ;
	rm -vfrd ./.mypy_cache 2>/dev/null || : ;
	rm -vfrd ./.pytest_cache 2>/dev/null || : ;

.PHONY: un-setup
un-setup:: full-clean
	rm -vfrd ./venv 2>/dev/null || : ;
