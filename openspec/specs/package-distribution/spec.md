# package-distribution Specification

## Purpose
What a consumer gets when installing `mapping-suite-sdk`: the Python versions it supports and how its runtime dependencies are declared. `DEC-n` references are the decisions in `openspec/changes/archive/2026-11-08-modernise-tooling-and-python/`.
## Requirements
### Requirement: Supported Python versions
The package SHALL declare `requires-python = ">=3.10,<3.14"` and SHALL install and import on
CPython 3.10, 3.11, 3.12 and 3.13 (modernise-tooling-and-python DEC-1).

#### Scenario: Install on Python 3.13
- **WHEN** a Python 3.13 project runs `pip install mapping-suite-sdk`
- **THEN** the install succeeds
- **AND** `import mapping_suite_sdk` succeeds

#### Scenario: Install on Python 3.10
- **WHEN** a Python 3.10 project runs `pip install mapping-suite-sdk`
- **THEN** the install succeeds
- **AND** `import mapping_suite_sdk` succeeds

### Requirement: Runtime dependencies are only what the code imports, as ranges
The package SHALL declare `pydantic` as its only runtime dependency and every other integration as an
extra: `mongodb` (`pymongo`), `github` (`gitpython`), `tracing` (`opentelemetry-api`,
`opentelemetry-sdk`), `cli` (`typer`) and `all` (the union of the four) (modular-core DEC-2). Every
declared distribution, runtime or extra, SHALL be imported by a module under `mapping_suite_sdk/` and
SHALL be a range with an upper bound at the next major version, never an exact pin
(modernise-tooling-and-python DEC-2, DEC-3).

#### Scenario: Core depends on pydantic only
- **WHEN** the runtime dependencies (no extra) of the installed distribution are read
- **THEN** they are exactly `pydantic`

#### Scenario: Extras map to integrations
- **WHEN** the extras of the installed distribution are read
- **THEN** `mongodb`, `github`, `tracing` and `cli` each declare the distributions named above
- **AND** `all` declares exactly the union of the four

#### Scenario: No unused runtime dependency
- **WHEN** the runtime and extra dependencies in `pyproject.toml` are compared with the top-level imports
  under `mapping_suite_sdk/`
- **THEN** every declared dependency is imported by at least one module

#### Scenario: No exact pin
- **WHEN** the runtime and extra dependency specifiers in `pyproject.toml` are read
- **THEN** none uses `==`
- **AND** each has an upper bound

#### Scenario: Resolves next to rdf-persistence
- **WHEN** a Python 3.13 project depends on both `mapping-suite-sdk[all]` and `rdf-persistence`
  (its `develop` branch)
- **THEN** the resolver finds one compatible set

