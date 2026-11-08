# Changelog

All notable changes to this project are documented here. Versions follow [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-11-08

### Added
- Python 3.13 support; the package installs and imports on Python 3.10, 3.11, 3.12 and 3.13 (#93).
- `make check-all`: one quality gate (Ruff, mypy, import-linter, LinkML codegen sync, tests with coverage ≥80%), run in CI on every supported Python.

### Changed
- Runtime dependencies are compatible ranges up to the next major version instead of exact pins: `pydantic>=2.10,<3`, `opentelemetry-api`/`opentelemetry-sdk>=1.29,<2`, `gitpython>=3.1,<4`, `pymongo>=4.11,<5`, `typer>=0.16,<1`.
- With `typer>=0.16` the CLI runs on Click 8.2+: `mssdk` with no arguments still prints help but now exits with code 2, and usage errors go to stderr.
- Generated `context.jsonld` files no longer carry the `comments` block with a generation timestamp.
- Developer tooling: Ruff replaces pylint, radon and xenon; tox is removed; Poetry >=2.2 with dependency groups `test`, `lint`, `model`.
- Models are generated with LinkML 1.12 (was 1.9.4), which lets the development lock use Click 8.5 like a fresh install does. In the generated `context.jsonld`, slots whose range is a class now declare `"@type": "@id"` instead of the class IRI. The RDF of every nested metadata and config object is unchanged; a class-ranged slot given as a plain string now becomes an IRI reference instead of a literal typed with the class.

### Removed
- Runtime dependencies that no module imports: `pandas`, `lxml`, `openpyxl`, `opentelemetry-instrumentation`, `click` (still installed through `typer`).
