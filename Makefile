SHELL=/bin/bash -o pipefail

BUILD_PRINT = \e[1;34m
END_BUILD_PRINT = \e[0m

ICON_DONE = [✔]
ICON_ERROR = [x]
ICON_WARNING = [!]
ICON_PROGRESS = [-]

NODE ?= $(shell command -v node)
NPM ?= $(shell command -v npm)
NPX ?= $(shell command -v npx)
DOC_BUILD_DIR=docs/build
ANTORA_PLAYBOOK := $(shell pwd)/docs/antora-playbook.local.yml
#-----------------------------------------------------------------------------
# Dev commands
#-----------------------------------------------------------------------------
build:
	@ echo -e "$(BUILD_PRINT)$(ICON_WARNING) Please do not build MSSDK in this project. This is not a good practice. Use another environment$(END_BUILD_PRINT)"

install: install-poetry
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing MSSDK requirements$(END_BUILD_PRINT)"
	@ poetry install --all-groups
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) MSSDK requirements are installed$(END_BUILD_PRINT)"

install-poetry:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing Poetry for MSSDK$(END_BUILD_PRINT)"
	@ pip install "poetry==2.0.1"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Poetry for MSSDK is installed$(END_BUILD_PRINT)"

test-unit:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running unit tests for MSSDK$(END_BUILD_PRINT)"
	@ poetry run tox
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Running unit tests for MSSDK done$(END_BUILD_PRINT)"

lint:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running Pylint checks for MSSDK$(END_BUILD_PRINT)"
	@ poetry run pylint --rcfile=.pylintrc ./mapping_suite_sdk ./tests
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Running Pylint checks for MSSDK done$(END_BUILD_PRINT)"

lint-report:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running Pylint checks and generating report for MSSDK$(END_BUILD_PRINT)"
	@ poetry run pylint --rcfile=.pylintrc --recursive=y ./mapping_suite_sdk ./tests | tail -n 3 | sed 's/^Your code/Pylint: Your code/' > pylint_report.txt || true
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Running Pylint checks and generating report for MSSDK done$(END_BUILD_PRINT)"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Report generated in pylint-report.txt$(END_BUILD_PRINT)"

lint-full-report:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running full Pylint checks and generating report for MSSDK$(END_BUILD_PRINT)"
	@ poetry run pylint --rcfile=.pylintrc ./mapping_suite_sdk ./tests | sed 's/^Your code/Pylint: Your code/' > pylint_report.txt || true
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Running full Pylint checks and generating report for MSSDK done$(END_BUILD_PRINT)"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Report generated in pylint-report.txt$(END_BUILD_PRINT)"

#-----------------------------------------------------------------------------
# Documentation commands
#-----------------------------------------------------------------------------
build-docs: run-antora

clean-docs:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Cleaning up Antora build...$(END_BUILD_PRINT)"
	@ rm -rfv $(DOC_BUILD_DIR)
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Antora build successfully cleaned!$(END_BUILD_PRINT)"

check-node:
ifeq ($(NODE),)
	@ echo -e "$(BUILD_PRINT)$(ICON_ERROR) Node.js is not installed. Please install Node.js first.$(END_BUILD_PRINT)"
	@ exit 1
else
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Node.js is installed: $(NODE)$(END_BUILD_PRINT)"
endif
ifeq ($(NPM),)
	@ echo -e "$(BUILD_PRINT)$(ICON_ERROR) npm is not installed. Please install npm first.$(END_BUILD_PRINT)"
	@ exit 1
else
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) npm is installed: $(NPM)$(END_BUILD_PRINT)"
endif


install-antora: check-node
	@echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing Antora locally...$(END_BUILD_PRINT)"
	npm install antora --save-dev
	@echo -e "$(BUILD_PRINT)$(ICON_DONE) Antora installed successfully!$(END_BUILD_PRINT)"


init-antora: install-antora
ifeq ($(wildcard package.json),)
	@echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Initializing Node.js project...$(END_BUILD_PRINT)"
	npm init -y
	@echo -e "$(BUILD_PRINT)$(ICON_DONE) package.json created.$(END_BUILD_PRINT)"
else
	@echo -e "$(BUILD_PRINT)$(ICON_DONE) package.json already exists.$(END_BUILD_PRINT)"
endif


run-antora: init-antora
	@echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Running Antora...$(END_BUILD_PRINT)"
	npx antora $(ANTORA_PLAYBOOK)
	@echo -e "$(BUILD_PRINT)$(ICON_DONE) Antora executed successfully!$(END_BUILD_PRINT)"
