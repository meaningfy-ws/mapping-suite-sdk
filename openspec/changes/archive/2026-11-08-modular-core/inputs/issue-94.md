# Seed: GitHub issue #94 — Modularise: a small core with optional extras for MongoDB, GitHub, tracing and the CLI

> Secondary input, preserved verbatim; the EPIC (proposal.md) supersedes it.
> Source: https://github.com/meaningfy-ws/mapping-suite-sdk/issues/94

## Summary
Make mapping-suite-sdk modular: a small core (package models, version detection, conversion, validation, hashing, folder and archive I/O) with no heavy or deployment-specific dependencies, and optional extras for MongoDB, GitHub, OpenTelemetry tracing and the CLI. Also stop configuring the root logger at import time.

## Context
- Consumer: Mapping Workbench 2. It stores data in a triple store and files in an S3 object store; it uses MSSDK only to load, validate, convert and build mapping packages. It never uses MongoDB, never loads from GitHub through MSSDK, has its own tracing, and does not use the CLI.
- mapping-suite-sdk commit: `ff6a66a` (develop).

## Current behaviour
- `pymongo` is a required dependency and is imported by the version-agnostic loader itself (`tools/services/load_mapping_package.py` imports `MongoClient` at module level; `persist_to_mongodb`, `mongo_client`, `database_name`, `collection_name` are parameters of `load_mapping_package`), and by every `save_mapping_package_v*` service.
- `gitpython` (only `core/adapters/extractor.py`), OpenTelemetry (only `core/adapters/tracer.py`) and `typer`/`click` (only the CLI) are required for every consumer.
- `mapping_suite_sdk/__init__.py` calls `logging.basicConfig(level=logging.INFO, ...)` on import, which reconfigures the logging of the application that imports the library.

## Proposed capability
```toml
[project]
dependencies = ["pydantic>=2.10,<3"]          # the core: models, detect, convert, validate, hash, folder/ZIP I/O

[project.optional-dependencies]
mongodb = ["pymongo>=4.11,<5"]
github  = ["gitpython>=3.1,<4"]
tracing = ["opentelemetry-api>=1.29,<2", "opentelemetry-sdk>=1.29,<2"]
cli     = ["typer>=0.15", "click>=8.1"]
all     = ["mapping-suite-sdk[mongodb,github,tracing,cli]"]
```
- The core modules import none of the optional libraries; MongoDB persistence moves out of `load_mapping_package` into separate functions (e.g. `save_mapping_package_to_mongodb(package, client, ...)`), so loading never touches pymongo.
- Using an optional feature without its extra raises a clear error: `ImportError: MongoDB support needs: pip install mapping-suite-sdk[mongodb]`.
- Tracing is a no-op when the `tracing` extra is absent.
- No `logging.basicConfig` in the library; it logs to its own named logger and leaves configuration to the application.
- Existing consumers (TED-SWS on Airflow) install `mapping-suite-sdk[all]` and keep working unchanged.

Intended use in a consumer:
```python
# pyproject: dependencies = ["mapping-suite-sdk"]   (core only)
from mapping_suite_sdk import load_mapping_package   # no pymongo, git or OpenTelemetry imported
package = load_mapping_package(path)
```

## Why it belongs in mapping-suite-sdk
Every consumer that is not the Airflow pipeline pays for MongoDB, GitHub, tracing and CLI dependencies it never calls, and inherits their version constraints. Only the library can split its own modules and extras; a consumer can only work around it by vendoring.

## Acceptance
- **Given** `pip install mapping-suite-sdk` (no extras), **when** a consumer loads, validates, converts and saves a v3 package, **then** it works and `pymongo`, `git` and `opentelemetry` are not importable from that environment.
- **Given** the core install, **when** a consumer calls a MongoDB function, **then** it gets an `ImportError` naming the `mongodb` extra.
- **Given** an application with its own logging configuration, **when** it imports `mapping_suite_sdk`, **then** its configuration is unchanged.
- **Given** `pip install mapping-suite-sdk[all]`, **when** the existing test suite runs, **then** it passes.

## Impact on the consumer
Not blocking alone, but MWB2 would otherwise carry MongoDB and the other dependencies in its API image. Related: the Python and dependency upgrade issue.

