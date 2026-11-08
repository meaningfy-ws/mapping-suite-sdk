# Seed: PLAN elicitation with the developer (2026-11-08)

> Secondary input, preserved; the EPIC and PLAN supersede it.

Context: `modernise-tooling-and-python` archived, 1.1.0 released. Brownfield probe (blocking `pymongo`,
`git`, `opentelemetry`, `typer`, `click` at import time) on `develop` @ `0938cdb`: 44 of 102 modules fail
to import — opentelemetry 15 (all via `core/adapters/tracer.py`), git 15 (via `core/adapters/extractor.py`,
which holds both `ArchiveExtractor` and `GitHubExtractor`), pymongo 11 (savers, save services, the two
repositories, `tools/services/load_mapping_package.py`), typer 3 (CLI).

Questions and answers:

1. *DEC-7 names `convert_mapping_package`, which does not exist* (there are `convert_mapping_package_model`,
   `convert_mapping_package_from_folder`, `convert_mapping_packages_from_folder`).
   → **Add a new version-agnostic `convert_mapping_package`.**
2. *Public surface — TED-SWS imports internal modules (asset classes, v3 and mapping-suite models,
   `core.adapters.repository`, `core.adapters.version_detector`, `mapping_suite.services.load_mapping_suite`).*
   → **Public = root exports + every `*.models` package; add `detect_mapping_package_version` and
   `load_mapping_suite_from_folder` to the root.** Adapters and services stay internal.
3. *What this change does about TED-SWS.* → **Open a migration issue in ted-rdf-conversion-pipeline
   (posted after developer approval).**
4. *Extra scenarios to prove* → **all four**: CLI without `[cli]` exits with a message naming the extra;
   explicit `add_span_processor_to_mssdk_tracer_provider` without `[tracing]` raises ImportError; with
   `MSSDK_TRACE` on and no OpenTelemetry, loading still works silently; `save_mapping_suite_to_mongo_db`
   is gated by `[mongodb]` too.

Standing criterion (developer, 2026-11-08): every module the change touches leaves the mypy ignore list
in `mypy.ini`. Estimated cost: 52 baseline errors in the likely-touched ignored modules, mostly local
`no-redef` / `assignment` / `union-attr`, plus 6 `attr-defined` in `core/adapters/repository.py`
(unbound `TypeVar`).
