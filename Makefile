SHELL=/bin/bash -o pipefail

BUILD_PRINT = \e[1;34m
END_BUILD_PRINT = \e[0m

PROJECT_PATH = $(shell pwd)
RESOURCES_PATH = ${PROJECT_PATH}/resources
SCHEMA_PATH ?= ${RESOURCES_PATH}/schema
TEMPLATES_PATH ?= ${RESOURCES_PATH}/templates
PYTHON_PATH ?= ${PROJECT_PATH}/mapping_suite_sdk

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
	@ poetry lock
	@ poetry install --all-groups
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) MSSDK requirements are installed$(END_BUILD_PRINT)"

install-poetry:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing Poetry for MSSDK$(END_BUILD_PRINT)"
	@ pip install "poetry==2.0.1"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Poetry for MSSDK is installed$(END_BUILD_PRINT)"

test-unit: generate-models
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


#-----------------------------------------------------------------------------
# LinkML Model Generation Commands
#-----------------------------------------------------------------------------

generate-models:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Generating Python models from LinkML schemas$(END_BUILD_PRINT)"
	@ $(MAKE) generate-models-recursive
	@ $(MAKE) optimize-models-imports
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Python models generated successfully$(END_BUILD_PRINT)"

optimize-models-imports:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Optimizing imports in generated models$(END_BUILD_PRINT)"
	@ find $(SCHEMA_PATH) -name "*.yaml" -type f | while read -r yaml_file; do \
		relative_path=$$(echo "$$yaml_file" | sed "s|^$(SCHEMA_PATH)/||"); \
		py_file="$(PYTHON_PATH)/$$(echo "$$relative_path" | sed 's|\.yaml$$|.py|')"; \
		if [ -f "$$py_file" ]; then \
			echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Optimizing imports in $$py_file$(END_BUILD_PRINT)"; \
			poetry run ruff check --select F401 --select I --fix "$$py_file" && \
			poetry run ruff format "$$py_file" || { \
				echo -e "$(BUILD_PRINT)$(ICON_WARNING) Failed to optimize $$py_file$(END_BUILD_PRINT)"; \
			}; \
		fi; \
	done
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Import optimization completed$(END_BUILD_PRINT)"

generate-models-recursive:
	@ find $(SCHEMA_PATH) -name "*.yaml" -type f | while read -r yaml_file; do \
		echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Processing $$yaml_file$(END_BUILD_PRINT)"; \
		relative_path=$$(echo "$$yaml_file" | sed "s|^$(SCHEMA_PATH)/||"); \
		output_dir="$(PYTHON_PATH)/$$(dirname "$$relative_path")"; \
		output_file="$(PYTHON_PATH)/$$(echo "$$relative_path" | sed 's|\.yaml$$|.py|')"; \
		echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Creating output directory: $$output_dir$(END_BUILD_PRINT)"; \
		mkdir -p "$$output_dir"; \
		echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Generating: $$output_file$(END_BUILD_PRINT)"; \
		poetry run gen-pydantic --meta None --template-dir $(TEMPLATES_PATH)/ "$$yaml_file" > "$$output_file.tmp" && mv "$$output_file.tmp" "$$output_file" || { \
			echo -e "$(BUILD_PRINT)$(ICON_ERROR) Failed to generate $$output_file$(END_BUILD_PRINT)"; \
			rm -f "$$output_file.tmp"; \
			exit 1; \
		}; \
		echo -e "$(BUILD_PRINT)$(ICON_DONE) Generated: $$output_file$(END_BUILD_PRINT)"; \
	done
