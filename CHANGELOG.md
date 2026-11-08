# Changelog

All notable changes to this project are documented here. Versions follow [Semantic Versioning](https://semver.org/).

## [2.1.0] - Unreleased

### Added
- `load_mapping_package_from_bytes(data, *, target_version="v3", include_output=False, validate_package=True)`:
  loads a package of any supported version from the bytes (or a binary stream) of its ZIP, without touching the
  disk. A ZIP with the package inside one wrapping folder loads like one with the package at its root; `__MACOSX/`
  entries are ignored.
- `mapping_package_to_zip_bytes(package)`, `save_mapping_package_v3_to_archive(package, path)` and
  `save_mapping_package_v3_to_folder(package, path)`: export a v3 package without a temp folder. They set
  `package.metadata.mapping_suite_hash_digest` on the passed package unless `update_hash=False`.
- All four are exported from `mapping_suite_sdk`.
- Safety: a ZIP with an absolute, `..` or backslash entry name, or more than 1 GiB uncompressed, is rejected with
  `ValueError("Failed to extract ZIP file: …")`. `save_mapping_package_v3_to_folder` serialises in memory first and
  rejects an asset path that would leave the folder, writing nothing.

## [2.0.0] - 2026-11-08

A major release: the core needs `pydantic` only, every integration is an extra, and saving is a separate
call (#94). TED-SWS and other 1.x consumers should pin `mapping-suite-sdk<2` until they migrate.

### Added
- Extras: `mongodb` (`pymongo`), `github` (`gitpython`), `tracing` (OpenTelemetry), `cli` (`typer`) and `all`.
  Calling an integration without its extra raises `ImportError` naming the extra; `mssdk` without `[cli]`
  exits with a one-line message.
- `save_mapping_package_to_mongodb(package, mongo_client, database_name, collection_name="mapping_package")`:
  saves a v3 or v3-lightweight package with the same document as 1.x's `persist_to_mongodb=True`, and upserts by
  id (1.x failed with `DuplicateKeyError` on a second save).
- `convert_mapping_package(package, to_version="v3")`: converts a loaded package to `"v3"` or `"v3L"` with the
  same rules as `load_mapping_package`.
- The public API is importable from the root: `load_mapping_package`, `validate_mapping_package`,
  `convert_mapping_package`, `detect_mapping_package_version`, `load_mapping_suite_from_folder`,
  `save_mapping_package_to_mongodb`, the v3 model classes and the typed errors (see `mapping_suite_sdk.__all__`).
  Names exported from the root and from any `*.models` package are the public API; adapters and services are
  internal and may change in a minor release.

### Changed
- **Breaking:** runtime dependencies are `pydantic` only. Install `mapping-suite-sdk[all]` to keep 1.x behaviour.
- **Breaking:** importing `mapping_suite_sdk` no longer calls `logging.basicConfig`. The library logs under the
  `mapping_suite_sdk` logger; the `mssdk` command configures logging itself.
- **Breaking:** `GitHubExtractor` moved from `mapping_suite_sdk.core.adapters.extractor` to
  `mapping_suite_sdk.core.adapters.github_extractor`.
- Without the `tracing` extra, traced operations run unchanged and produce no spans, even with `MSSDK_TRACE=true`.
- `make check-all` also builds the wheel and runs `tests/core_only` against it with no extras installed.

### Removed
- **Breaking:** `load_mapping_package` no longer accepts `persist_to_mongodb`, `mongo_client`, `database_name` or
  `collection_name`.

### Migrating from 1.x

| 1.x | 2.0 |
|---|---|
| `pip install mapping-suite-sdk` | `pip install "mapping-suite-sdk[all]"` (or only the extras you use) |
| `load_mapping_package(path, persist_to_mongodb=True, mongo_client=c, database_name=db, collection_name=coll)` | `pkg = load_mapping_package(path)` then `save_mapping_package_to_mongodb(pkg, c, db, coll)` |
| `from mapping_suite_sdk.core.adapters.extractor import GitHubExtractor` | `from mapping_suite_sdk.core.adapters.github_extractor import GitHubExtractor` |
| Relying on the SDK import to configure logging | Call `logging.basicConfig(...)` in your application |
| `from mapping_suite_sdk.tools.services.load_mapping_package import load_mapping_package` | Still works; `from mapping_suite_sdk import load_mapping_package` is the stable path |

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
