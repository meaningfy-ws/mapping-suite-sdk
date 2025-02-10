SHELL=/bin/bash -o pipefail
BUILD_PRINT = \e[1;34mSTEP:
END_BUILD_PRINT = \e[0m

#-----------------------------------------------------------------------------
# Dev commands
#-----------------------------------------------------------------------------
install: install-poetry
	@ echo -e "$(BUILD_PRINT)Installing the requirements$(END_BUILD_PRINT)"
	@ poetry install --no-root

install-dev: install-poetry
	@ echo -e "$(BUILD_PRINT)Installing the requirements$(END_BUILD_PRINT)"
	@ poetry install --only dev --no-root

install-poetry:
	@ echo -e "$(BUILD_PRINT)Installing Poetry$(END_BUILD_PRINT)"
	@ curl -sSL https://install.python-poetry.org | python3 -

test-unit:
	@ echo -e "$(BUILD_PRINT)Running Unit tests$(END_BUILD_PRINT)"
	@ tox