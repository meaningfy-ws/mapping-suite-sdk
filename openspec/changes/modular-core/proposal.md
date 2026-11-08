# EPIC: Modular core with optional extras (MSSDK 2.0.0)

Closes #94. Depends on `modernise-tooling-and-python` (lands first: same `pyproject.toml`, and its
gate proves this change on 3.10–3.13).

## Appetite

LARGE — several capabilities move (persistence leaves the loader, three integrations become
optional, the public API is defined), with a breaking release.

## Why

Every consumer pays for MongoDB, GitHub, OpenTelemetry and CLI dependencies it may never call:
`pymongo` is imported by the version-agnostic loader itself, and `mapping_suite_sdk/__init__.py`
calls `logging.basicConfig`, reconfiguring the importing application's logging. Mapping Workbench 2
needs only load / validate / convert / hash / serialise and must not carry the rest into its API
image.

## Solution outline

`pip install mapping-suite-sdk` gives a core that loads, validates, converts, hashes and serialises
packages with only `pydantic` installed. MongoDB, GitHub extraction, tracing and the CLI each come
from an extra. Calling an integration without its extra fails with an error naming the extra;
tracing silently becomes a no-op. Importing the library no longer touches logging configuration.
The functions consumers use are importable from `mapping_suite_sdk` directly.

## Key decisions

- **DEC-1**: Release as **2.0.0, a clean break** — `persist_to_mongodb`, `mongo_client`,
  `database_name`, `collection_name` leave `load_mapping_package`; TED-SWS pins `<2` until it adopts
  `mapping-suite-sdk[mongodb]`. Rejected: 1.x deprecation path (more code for one consumer we control).
- **DEC-2**: Extras: `mongodb` (pymongo), `github` (gitpython), `tracing` (opentelemetry-api/-sdk),
  `cli` (typer), `all` (the four). Core runtime dependency: `pydantic` only.
- **DEC-3**: Persistence is a separate call: `save_mapping_package_to_mongodb(package, client, …)`
  (version-agnostic, dispatching on the package type); the per-version `save_mapping_package_v*_to_mongo_db`
  stay, behind the `mongodb` extra.
- **DEC-4**: Optional imports are lazy at the integration boundary (the adapter module), and a
  missing extra raises `ImportError("<feature> support needs: pip install mapping-suite-sdk[<extra>]")`.
  Rejected: import-time feature flags in config.
- **DEC-5**: Tracing degrades to a no-op when `opentelemetry` is absent; the decorators stay in place.
- **DEC-6**: The library logs only to `logging.getLogger("mapping_suite_sdk")` (and children) and
  never calls `basicConfig` or adds handlers.
- **DEC-7**: `mapping_suite_sdk/__init__.py` re-exports the public API — `load_mapping_package`,
  `validate_mapping_package`, `convert_mapping_package`, the v3 model classes, the typed errors and
  `save_mapping_package_to_mongodb` (lazy). Everything else is internal and may change without a major.
- **DEC-7a** (re-shape of DEC-7, 2026-11-08, see `inputs/planning-qa-2026-11-08.md`): the root also
  exports a **new** version-agnostic `convert_mapping_package(package, to_version="v3")` (DEC-7 named a
  function that did not exist), `detect_mapping_package_version` and `load_mapping_suite_from_folder`.
  The public surface is the root exports **plus every `*.models` package** (TED-SWS builds on the model
  and asset classes); adapters and services are internal. Rejected: root-only (a long re-export list),
  everything public (any refactor becomes a major).
- **DEC-8**: import-linter gains a contract: core modules (models, loaders, converters, validators,
  hashers, serialisers) MUST NOT import `pymongo`, `git`, `opentelemetry` or `typer`.

## Rabbit-holes

- `core/adapters/extractor.py` holds both the archive and the GitHub extractor: split the module
  rather than guard inside it.
- `core/adapters/tracer.py` is imported by ~30 modules; the no-op must keep the same decorator API
  so those modules do not change.
- Test isolation: proving "pymongo not importable" needs a clean virtualenv in CI, not import
  mocking.

## No-gos

- No new persistence backends (S3, triple store) — consumers own those.
- No change to the package formats, the hash algorithm or version detection.
- No 1.x compatibility shims.
- No in-memory I/O — that is `in-memory-package-io` (#95).
- No redesign of test-data storage (#27, parked).

---

## What Changes

- **BREAKING** `load_mapping_package` loses `persist_to_mongodb`, `mongo_client`, `database_name`,
  `collection_name`; new `save_mapping_package_to_mongodb`.
- **BREAKING** `pymongo`, `gitpython`, `opentelemetry-*`, `typer` move to extras; `pip install
  mapping-suite-sdk[all]` restores 1.x behaviour.
- **BREAKING** importing MSSDK no longer configures the root logger.
- Public API re-exported from `mapping_suite_sdk`.
- `make check-all` (so CI, on every Python) installs the core only in a fresh venv and asserts the optional libraries are absent (design P-10: one gate, no separate job).
- Migration note in CHANGELOG and docs (TED-SWS).

## Capabilities

### New Capabilities
- `optional-integrations`: which features need which extra, and how a missing extra behaves.
- `public-api`: the names importable from `mapping_suite_sdk` and the logging contract.
- `mongodb-persistence`: saving a loaded package to MongoDB as a separate call.

### Modified Capabilities
- `package-distribution`: the runtime dependency is `pydantic` only; integrations move to extras.
- `developer-tooling`: `make check-all` also proves the core works with no extras installed.


## Impact

- TED-SWS: a migration issue is opened in ted-rdf-conversion-pipeline (DEC-7a Q&A). It must switch to `mapping-suite-sdk[all]` and call `save_mapping_package_to_mongodb`
  after loading; pins `<2` until then.
- MWB2: depends on the core only.
- Docs: `mongodb-support.adoc`, `opentelemetry-tracing.adoc`, `cli.adoc`, `quick-start.adoc`.
