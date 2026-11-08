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
	@ poetry install --all-groups --all-extras
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) MSSDK requirements are installed$(END_BUILD_PRINT)"

install-poetry:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing Poetry for MSSDK$(END_BUILD_PRINT)"
	@ pip install "poetry>=2.2,<3"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Poetry for MSSDK is installed$(END_BUILD_PRINT)"

#-----------------------------------------------------------------------------
# Quality gate — `make check-all` is what CI runs on every supported Python
#-----------------------------------------------------------------------------
.PHONY: check-all lint format typecheck check-architecture check-codegen test test-unit test-core-only

check-all: lint typecheck check-architecture check-codegen test test-core-only
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) All quality checks passed!$(END_BUILD_PRINT)"

lint:
	@ poetry run ruff check .
	@ poetry run ruff format --check .

format:
	@ poetry run ruff check --fix .
	@ poetry run ruff format .

typecheck:
	@ poetry run mypy mapping_suite_sdk

check-architecture:
	@ poetry run lint-imports

# Regenerates the LinkML models and fails if that changes anything (P-4).
check-codegen:
	@ git diff --quiet -- mapping_suite_sdk resources/schema || { \
		echo -e "$(BUILD_PRINT)$(ICON_ERROR) Uncommitted changes in mapping_suite_sdk/ or resources/schema/: commit or stash first$(END_BUILD_PRINT)"; \
		exit 1; }
	@ $(MAKE) --no-print-directory generate-models > /dev/null
	@ git diff --exit-code --stat -- mapping_suite_sdk resources/schema || { \
		echo -e "$(BUILD_PRINT)$(ICON_ERROR) Generated models are out of sync with the LinkML schemas: run make generate-models and commit the result$(END_BUILD_PRINT)"; \
		exit 1; }
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Generated models are in sync$(END_BUILD_PRINT)"

test:
	@ poetry run pytest --cov=mapping_suite_sdk --cov-report=term-missing:skip-covered --cov-report=xml --cov-fail-under=80

test-unit: test

# The built wheel with no extras, in a fresh venv: proves the core needs pydantic only. -c /dev/null,
# --noconftest, importlib mode and running from temp/ keep the source tree off sys.path.
test-core-only:
	@ rm -rf dist temp/core-only-venv
	@ poetry build --format wheel
	@ $$(poetry env info -e) -m venv temp/core-only-venv
	@ temp/core-only-venv/bin/pip install --quiet dist/*.whl pytest
	@ cd temp && core-only-venv/bin/python -I -m pytest -c /dev/null --noconftest --import-mode=importlib \
		-p no:cacheprovider --rootdir=.. ../tests/core_only

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
		\
		context_output_dir="$$(dirname "$$yaml_file")"; \
		context_output_file="$$context_output_dir/context.jsonld"; \
		if [ -f "$$yaml_file" ]; then \
			echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Generating JSON-LD context: $$context_output_file$(END_BUILD_PRINT)"; \
			poetry run gen-jsonld-context --no-metadata "$$yaml_file" > "$$context_output_file.tmp" && mv "$$context_output_file.tmp" "$$context_output_file" || { \
				echo -e "$(BUILD_PRINT)$(ICON_WARNING) Failed to generate context.jsonld for $$yaml_file$(END_BUILD_PRINT)"; \
				rm -f "$$context_output_file.tmp"; \
			}; \
			if [ -f "$$context_output_file" ]; then \
				echo -e "$(BUILD_PRINT)$(ICON_DONE) Generated: $$context_output_file$(END_BUILD_PRINT)"; \
			fi; \
		fi; \
	done

generate-model-view:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Generating schemas and diagrams from LinkML schemas$(END_BUILD_PRINT)"
	@ mkdir -p tmp/diagrams
	@ mkdir -p tmp/schemas
	@ find $(SCHEMA_PATH) -name "*.yaml" -type f | while read -r yaml_file; do \
		base_name=$$(basename "$$yaml_file" .yaml); \
		relative_path=$$(echo "$$yaml_file" | sed "s|^$(SCHEMA_PATH)/||" | sed 's|/|_|g' | sed 's|\.yaml$$||'); \
		echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Generating schemas and diagrams for $$yaml_file$(END_BUILD_PRINT)"; \
		echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) - Generating PlantUML (UML class diagram): tmp/diagrams/$${relative_path}.puml$(END_BUILD_PRINT)"; \
		poetry run gen-plantuml "$$yaml_file" > "tmp/diagrams/$${relative_path}.puml" || { \
			echo -e "$(BUILD_PRINT)$(ICON_WARNING) Failed to generate PlantUML for $$yaml_file$(END_BUILD_PRINT)"; \
		}; \
		echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) - Generating JSON Schema: tmp/schemas/$${relative_path}_schema.json$(END_BUILD_PRINT)"; \
		base_class=$$(grep "^id:" "$$yaml_file" | head -1 | awk '{print $$2}'); \
		poetry run gen-json-schema --closed --top-class "$$base_class" "$$yaml_file" > "tmp/schemas/$${relative_path}_schema.json" || { \
			echo -e "$(BUILD_PRINT)$(ICON_WARNING) Failed to generate JSON Schema for $$yaml_file$(END_BUILD_PRINT)"; \
		}; \
		echo -e "$(BUILD_PRINT)$(ICON_DONE) Generated schemas and diagrams for $$base_name$(END_BUILD_PRINT)"; \
	done
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) All diagrams and schemas generated$(END_BUILD_PRINT)"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) - UML diagrams (PlantUML .puml files) in: tmp/diagrams/$(END_BUILD_PRINT)"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) - JSON Schemas (.json files) in: tmp/schemas/$(END_BUILD_PRINT)"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) - View PlantUML at: https://www.plantuml.com/plantuml/uml/$(END_BUILD_PRINT)"
