SHELL=/bin/bash -o pipefail
BUILD_PRINT = \e[1;34mSTEP:
END_BUILD_PRINT = \e[0m

#-----------------------------------------------------------------------------
# User commands
#-----------------------------------------------------------------------------
install: install-poetry
	@ echo -e "$(BUILD_PRINT)Installing MSSDK$(END_BUILD_PRINT)"
	@ poetry install --without dev,docs --no-root
#-----------------------------------------------------------------------------
# Dev commands
#-----------------------------------------------------------------------------
install-all: install-poetry
	@ echo -e "$(BUILD_PRINT)Installing the requirements$(END_BUILD_PRINT)"
	@ poetry install --all-groups --no-root

install-docs: install-poetry
	@ echo -e "$(BUILD_PRINT)Installing docs requirements$(END_BUILD_PRINT)"
	@ poetry install --only docs --no-root

install-dev: install-poetry
	@ echo -e "$(BUILD_PRINT)Installing dev requirements$(END_BUILD_PRINT)"
	@ poetry install --only dev --no-root

install-poetry:
	@ echo -e "$(BUILD_PRINT)Installing Poetry$(END_BUILD_PRINT)"
	@ pip install "poetry==2.0.1"

test-unit:
	@ echo -e "$(BUILD_PRINT)Running Unit tests$(END_BUILD_PRINT)"
	@ poetry run tox

lint:
	@ echo -e "$(BUILD_PRINT)Running Pylint check$(END_BUILD_PRINT)"
	@ poetry run pylint --rcfile=.pylintrc ./mapping_suite_sdk ./tests

lint-report:
	@ echo -e "$(BUILD_PRINT)Running Pylint check and generating report$(END_BUILD_PRINT)"
	@ poetry run pylint --rcfile=.pylintrc --recursive=y ./mapping_suite_sdk ./tests | tail -n 3 | sed 's/^Your code/Pylint: Your code/' > pylint_report.txt || true
	@ echo "Report generated in pylint-report.txt"

lint-full-report:
	@ echo -e "$(BUILD_PRINT)Running Pylint check and generating report$(END_BUILD_PRINT)"
	@ poetry run pylint --rcfile=.pylintrc ./mapping_suite_sdk ./tests | sed 's/^Your code/Pylint: Your code/' > pylint_report.txt || true
	@ echo "Report generated in pylint-report.txt"

create-requirements-txt:
	@ echo -e "$(BUILD_PRINT)Generating requirements.txt$(END_BUILD_PRINT)"
	@ pip freeze > requirements.txt
	@ echo "$(BUILD_PRINT)Generating requirements.txt DONE$(END_BUILD_PRINT)"