## MODIFIED Requirements

### Requirement: One quality gate
The repository SHALL provide `make check-all`, which runs, and fails if any fails: Ruff lint and
format check, mypy, import-linter, the LinkML codegen-sync check, the test suite with a
coverage floor of 80%, and the core-only check, which installs the built wheel with no extras into a
fresh virtual environment and runs the core-only tests there (modernise-tooling-and-python DEC-4,
DEC-6; modular-core DEC-2).

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

#### Scenario: A core module importing an optional library fails the gate
- **WHEN** a core module (for example a loader) imports `pymongo` at module level
- **THEN** `make check-all` exits non-zero
