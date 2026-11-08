## ADDED Requirements

### Requirement: One quality gate
The repository SHALL provide `make check-all`, which runs, and fails if any fails: Ruff lint and
format check, mypy, import-linter, the LinkML codegen-sync check, and the test suite with a
coverage floor of 80% (DEC-4, DEC-6).

#### Scenario: Gate passes on a clean checkout
- **WHEN** a developer runs `make install` then `make check-all` on a clean checkout of `develop`
- **THEN** every check runs
- **AND** the command exits 0

#### Scenario: A lint violation fails the gate
- **WHEN** a module under `mapping_suite_sdk/` contains an unused import
- **THEN** `make check-all` exits non-zero and names the file

#### Scenario: Generated models out of sync fail the gate
- **WHEN** a LinkML schema under `resources/schema/` changes and the generated module is not regenerated
- **THEN** `make check-all` exits non-zero and says to run `make generate-models`

#### Scenario: Coverage below the floor fails the gate
- **WHEN** test coverage of `mapping_suite_sdk` is below 80%
- **THEN** `make check-all` exits non-zero

### Requirement: Tool configuration in dedicated root files
Each tool SHALL be configured in its own file at the repository root (`ruff.toml`, `mypy.ini`,
`pytest.ini`, `.coveragerc`, `.importlinter`), and `pyproject.toml` SHALL contain no `[tool.*]`
table other than `[tool.poetry]` (DEC-5).

#### Scenario: pyproject carries no tool config
- **WHEN** `pyproject.toml` is read
- **THEN** its only `tool` table is `[tool.poetry]`

### Requirement: CI runs the same gate on every supported Python
CI SHALL run `make check-all` on every pull request and push to `develop`, once per Python version
3.10, 3.11, 3.12 and 3.13 (DEC-1).

#### Scenario: Pull request on four Pythons
- **WHEN** a pull request into `develop` is opened
- **THEN** CI runs `make check-all` on Python 3.10, 3.11, 3.12 and 3.13
- **AND** the pull request shows one check per version
