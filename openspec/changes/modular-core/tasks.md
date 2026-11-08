> Derives from: EPIC `modular-core` ([proposal.md](proposal.md), closes #94)
> Document type: implementation PLAN (tasks half); pair: [design.md](design.md). Specs: [optional-integrations](specs/optional-integrations/spec.md), [public-api](specs/public-api/spec.md), [mongodb-persistence](specs/mongodb-persistence/spec.md), [package-distribution](specs/package-distribution/spec.md), [developer-tooling](specs/developer-tooling/spec.md).

## 1. Guard helper

- [x] 1.1 Add `core/adapters/optional_dependency.py` with `require()` (P-1) and a unit test for both paths (module present; missing module → message names feature and extra)

## 2. Integration boundaries (existing suite green after each)

- [ ] 2.1 Tracing: guarded OpenTelemetry import and no-op decorators in `tracer.py`; `add_span_processor_to_mssdk_tracer_provider` calls `require` (P-4)
- [ ] 2.2 GitHub: move `GitHubExtractor` to `core/adapters/github_extractor.py` with `require` inside its methods; update the 9 importers (P-3)
- [ ] 2.3 MongoDB: `pymongo` imports under `TYPE_CHECKING` in the repositories, savers, save and load services; `require` in `MongoDBRepository.__init__` and as the first statement of every `save_*_to_mongo_db`, incl. `save_mapping_suite_to_mongo_db` (P-2)
- [ ] 2.4 CLI: guarded `typer` import in `cli/__init__.py` raising `SystemExit` with the `[cli]` message; root callback configures logging (P-5)

## 3. MongoDB persistence (BREAKING)

- [ ] 3.1 Run the one-off golden-capture script and commit `tests/test_data/mongodb_golden/{v3,v3L}.json` (P-13)
- [ ] 3.2 Add `save_mapping_package_to_mongodb` (P-7) with tests for "Same document as 1.x" (against the golden files) and "Saving twice updates in place"
- [ ] 3.3 Remove `persist_to_mongodb`, `mongo_client`, `database_name`, `collection_name`, `_persist_to_mongodb`, `_persist_if_requested` from `load_mapping_package`; test "Old parameter rejected"; update callers and tests (DEC-1)

## 4. Public API, extras, gate

- [ ] 4.1 `convert_mapping_package` with the moves listed in P-6; `validate_mapping_package` wraps `VersionDetectionError`; `load_mapping_package` calls `convert_mapping_package`; tests for the five public-api convert scenarios
- [ ] 4.2 Root exports + `__all__` (P-8); remove `logging.basicConfig` from the root (DEC-6); test "Application logging unchanged" in the normal suite **in a subprocess** (`python -c` that configures the root logger, imports `mapping_suite_sdk`, prints level + handler count)
- [ ] 4.3 Extras and version 2.0.0 in `pyproject.toml` (P-11), `make install` with `--all-extras`, `poetry lock`; update `tests/unit/test_package_metadata.py` for "Core depends on pydantic only", "Extras map to integrations", "No unused runtime dependency", "No exact pin"
- [ ] 4.4 `make test-core-only` per P-10 (no `__init__.py` in `tests/core_only/`), first test `tests/core_only/test_import.py`: "Import the loader from the root" with `find_spec` absence checks; add to `check-all`; `--ignore=tests/core_only` in `pytest.ini`; delete the wheel-install step from `ci.yaml` (developer-tooling: One quality gate)
- [ ] 4.5 import-linter contract with the ignore lines exactly as in P-9; check by hand once that a module-level `import pymongo` in a loader fails `make check-all` ("A core module importing an optional library fails the gate"), note it in the PR

## 5. Core-only proof

- [ ] 5.1 `tests/core_only/` scenarios: core-only round trip (v2 folder → load → convert → validate); ImportError messages for `save_mapping_package_to_mongodb`, a `load_mapping_packages_*_from_github` function, `save_mapping_suite_to_mongo_db` (repository argument `None`; `require` runs first) and `add_span_processor_to_mssdk_tracer_provider`; `mssdk` without `[cli]` (subprocess, exit ≠ 0, message, no `Traceback` in stderr); load with and without `MSSDK_TRACE=true` emits no warning (`warnings.catch_warnings(record=True)` list empty, and no `caplog` record at WARNING or above); "Model modules stay importable by path" (optional-integrations, public-api)
- [ ] 5.2 `make check-all` green on 3.10 and 3.13 locally

## 6. Type debt, docs, release notes

- [ ] 6.1 Remove every touched module from `mypy.ini` and make `make typecheck` green (P-12); this prints nothing: `git diff --name-only develop...HEAD -- mapping_suite_sdk | sed 's|/__init__\.py$||; s|\.py$||; s|/|.|g' | sort | comm -12 - <(grep -oP '(?<=^\[mypy-)[^\]]+' mypy.ini | tr , '\n' | sort)`
- [ ] 6.2 Docs: `quick-start.adoc`, `index.adoc` (install with extras), `mongodb-support.adoc`, `extractors.adoc` (GitHub extra), `opentelemetry-tracing.adoc`, `cli.adoc`, `serialisation.adoc` (any persistence mention); README install section; CHANGELOG 2.0.0 with a migration section (DEC-1, DEC-7a public surface)
- [ ] 6.3 Rerun the rdf-persistence co-resolution with `mapping-suite-sdk[all]` on 3.13 (package-distribution: Resolves next to rdf-persistence); paste in the PR
- [ ] 6.4 TED-SWS migration issue text in the PR description; post it after developer approval (P-14)

## Roadmap

- [x] 1.1 · [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 2.4 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 4.4 · [ ] 4.5 · [ ] 5.1 · [ ] 5.2 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 6.4

## Verification

`make check-all` green locally on 3.10 and 3.13 and in the CI matrix (includes the core-only check); `openspec validate modular-core --strict`; clarity gate ≥9/10 on design.md + tasks.md.
