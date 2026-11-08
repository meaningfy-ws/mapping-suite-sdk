> Derives from: EPIC `modular-core` ([proposal.md](proposal.md), closes #94)
> Document type: implementation PLAN (design half); pair: [tasks.md](tasks.md).

## Context

Baseline: `develop` @ `0938cdb` (1.1.0 released), Python 3.12, `make check-all` green, 963 tests,
coverage 96.68%, mypy ignores 41 modules (`mypy.ini`, shortcut note pointing here).

Core-only probe (block `pymongo`, `bson`, `git`, `gitdb`, `opentelemetry`, `typer`, `click` at import
time, import every module): **44 of 102 modules fail**, from four roots:

| Root | Modules broken | Why |
|---|---|---|
| `core/adapters/tracer.py` imports OpenTelemetry at module level | 15 | every loader/serialiser/validator uses `@traced_routine` / `@traced_class` (38 importers) |
| `core/adapters/extractor.py` imports `git` at module level | 15 | it holds `ArchiveExtractor` (core) **and** `GitHubExtractor`; 12 services import it |
| `pymongo` imported for **type hints only** | 11 | `repository.py`, `package_repository.py`, the 4 savers, 4 save services, `tools/services/load_mapping_package.py`; load services import `MongoDBRepository` only to annotate `*_from_mongo_db` |
| `typer` | 3 | the CLI modules |

Other facts the plan relies on:
- `mapping_suite_sdk/__init__.py` calls `logging.basicConfig(level=INFO, …)`. All 27 library modules
  already log through `logging.getLogger(__name__)` (children of `mapping_suite_sdk`). The CLI's
  `typer_verbose_callback` sets the root logger to DEBUG.
- Conversion: `convert_mapping_package_model(from, to, pkg)` supports v1→v3, v1→v3L, v2→v3, v2→v3L,
  v3→v3L; `validate_mapping_package._detect_version_from_model` maps a model to its `Version`;
  `load_mapping_package._validate_conversion_path` rejects v3L→v3; same version skips conversion.
- `_persist_to_mongodb` (in `load_mapping_package`) dispatches on the package type to
  `save_mapping_package_v3_to_mongo_db` / `save_mapping_package_v3_lightweight_to_mongo_db`.
- TED-SWS imports `core.models.collection_asset`, `core.models.file_asset`, the v3 and mapping-suite
  model modules, `core.adapters.repository`, `core.adapters.version_detector`,
  `mapping_suite.services.load_mapping_suite`, `tools.services.load_mapping_package` (inputs Q&A).
- import-linter 2.9 is installed; it supports `include_external_packages` and
  `exclude_type_checking_imports`.

## Goals / Non-Goals

**Goals:** the capabilities in the spec deltas — `optional-integrations`, `public-api`,
`mongodb-persistence` (new), `package-distribution` and `developer-tooling` (modified) — released as
**2.0.0**.

**Non-Goals:** everything in the EPIC's No-gos.

## Decisions

Settled in the EPIC: DEC-1 (2.0.0 clean break), DEC-2 (extras), DEC-3 (separate save call), DEC-4 (lazy
at the adapter boundary, `ImportError` naming the extra), DEC-5 (tracing no-op), DEC-6 (no logging
config), DEC-7 + DEC-7a (root exports, public surface = root + `*.models`, new `convert_mapping_package`),
DEC-8 (import-linter contract).

New, made while planning:

- **P-1 One guard helper.** New `mapping_suite_sdk/core/adapters/optional_dependency.py` with
  `require(module: str, extra: str, feature: str) -> ModuleType`: `importlib.import_module(module)`, and
  on `ImportError` raises `ImportError(f"{feature} support needs: pip install mapping-suite-sdk[{extra}]")`
  `from` the original. Every integration calls it at the point of use. Rejected: a `try/except` copied
  into each module (eight copies of the same message).
- **P-2 MongoDB boundary.** `pymongo` imports in the two repositories, the four savers, the save services
  and the load services move under `if TYPE_CHECKING:` (`from __future__ import annotations` already
  present or added). `MongoDBRepository.__init__` and each `save_*_to_mongo_db` start with
  `require("pymongo", "mongodb", "MongoDB")`. The `*_from_mongo_db` loaders take a repository instance,
  which cannot exist without the extra, so they need no guard.
- **P-3 GitHub boundary.** `GitHubExtractor` moves to a new `core/adapters/github_extractor.py`;
  `extractor.py` keeps `ExtractorABC` + `ArchiveExtractor` and no `git` import. `github_extractor.py`
  imports `git` only inside its methods via `require("git", "github", "GitHub")`; `Repo` annotations
  go under `TYPE_CHECKING`. Services keep importing `GitHubExtractor` at module top (now harmless).
  This is the EPIC rabbit-hole's "split the module".
- **P-4 Tracing boundary.** `tracer.py` does `try: from opentelemetry import trace … except ImportError:
  trace = None`. With no OpenTelemetry: `traced_routine` / `traced_class` return the function/class
  unchanged, `_MSSDK_TRACER_PROVIDER` is `None`, `set/get_mssdk_tracing` and
  `is_mssdk_tracing_enabled` still work (env flag only), and `add_span_processor_to_mssdk_tracer_provider`
  calls `require("opentelemetry.sdk.trace", "tracing", "Tracing")`. The decision is taken **at import
  time**, so decorated functions keep their exact current wrapper when OpenTelemetry is present.
- **P-5 CLI boundary.** `tools/entrypoints/cli/__init__.py` starts with a guarded `import typer`; on
  `ImportError` it raises `SystemExit("The mssdk command needs: pip install mapping-suite-sdk[cli]")`.
  The console script imports this package first, so a core-only `mssdk` prints one line and exits 1 —
  no traceback (spec scenario). `SystemExit`, not `ImportError`, because a console script is an
  application. The CLI is an application, so its root callback now calls `logging.basicConfig(level=INFO,
  format=mssdk_config.MSSDK_LOGGING_STRING_FORMAT, datefmt=mssdk_config.MSSDK_DATE_FORMAT)` — the
  configuration the library root used to do — and `--verbose` keeps setting DEBUG.
- **P-6 `convert_mapping_package`.** In `tools/services/convert_mapping_package.py`:
  `convert_mapping_package(mapping_package, to_version: str = "v3")`. What moves **into** that module
  (it already holds `Version`, `ConversionError`, `UnsupportedVersionError`; moving the rest there
  avoids a cycle, because `validate_mapping_package.py` already imports it):
  - `UnsupportedConversionError` and `VersionDetectionError` (today in `load_mapping_package.py`, which
    re-imports them so `from …load_mapping_package import UnsupportedConversionError` keeps working);
  - `load_mapping_package._normalize_version` (raises `UnsupportedVersionError`) as `_normalize_version`;
    `validate_mapping_package._normalize_version` (raises `CrossVersionValidationError`) stays where it is;
  - `load_mapping_package._validate_conversion_path`;
  - `validate_mapping_package._detect_version_from_model`, now raising **`VersionDetectionError`**
    for any object that is not one of the four package classes (it raised `CrossVersionValidationError`,
    defined in `validate_mapping_package.py` — keeping that would import validate from convert, a
    cycle). `validate_mapping_package` keeps its behaviour: it imports the helper and wraps the call,
    `except VersionDetectionError as err: raise CrossVersionValidationError(str(err)) from err`.

  Steps of `convert_mapping_package`: `_normalize_version(to_version)`, and any target other than v3 / v3L → `UnsupportedVersionError` (the spec allows only those two; packages are never down-converted to v1/v2);
  source = `_detect_version_from_model(mapping_package)` (not a package → `VersionDetectionError`);
  `_validate_conversion_path(source, target)` (v3L→v3 → `UnsupportedConversionError`); same version →
  return the input object; else `convert_mapping_package_model(source, target, mapping_package)`.
  `load_mapping_package` then calls `convert_mapping_package`, so the two cannot drift.
- **P-7 Version-agnostic save.** New `tools/services/save_mapping_package.py` with
  `save_mapping_package_to_mongodb(mapping_package, mongo_client, database_name,
  collection_name="mapping_package")`: `require(...)`; any type other than `MappingPackageV3` /
  `MappingPackageV3Lightweight` → `UnsupportedConversionError`, as 1.x raises today; then
  `PackageRepository(...).upsert(package)`. *Corrected during apply:* 1.x's `_persist_to_mongodb`
  went through the savers' `create` (`insert_one`), so a second save raised `DuplicateKeyError`; the
  spec's "Saving twice updates in place" needs the upsert. The stored document is the same
  (`replace_one` of the same `model_dump`), which the golden test proves. The version-specific savers
  keep their 1.x insert behaviour. `_persist_to_mongodb` and `_persist_if_requested` are deleted.
- **P-8 Root exports** (`mapping_suite_sdk/__init__.py`, plus `__all__`): `__version__`, `mssdk_config`,
  `MSSDKConfigResolver` (kept), `load_mapping_package`, `validate_mapping_package`,
  `convert_mapping_package`, `detect_mapping_package_version`, `load_mapping_suite_from_folder`,
  `save_mapping_package_to_mongodb`, `MappingPackageV3`, `MappingPackageV3Lightweight`,
  `MappingPackageV3Metadata`, `MappingPackageV3MetadataJSONLD`, `ApplicabilityConstraints`,
  `VersionRange`, `DateTimeInterval`, and the errors `ConversionError`, `UnsupportedVersionError`,
  `UnsupportedConversionError`, `VersionDetectionError`, `InvalidPackagePathError`,
  `MPValidationException`, `CrossVersionValidationError`, `MPV3StructuralValidationException`,
  `MPV3HashValidationException`. `config` stays imported first (services read `mssdk_config` from the
  root at import time).
- **P-9 import-linter contract (DEC-8).** `.importlinter` gets `include_external_packages = True` and
  `exclude_type_checking_imports = True`, and one `forbidden` contract: source `mapping_suite_sdk`,
  forbidden `pymongo`, `git`, `opentelemetry`, `typer`, with `ignore_imports` for exactly the boundary
  edges, written the way import-linter matches external packages (collapsed to the top-level name):
  `mapping_suite_sdk.core.adapters.tracer -> opentelemetry`,
  `mapping_suite_sdk.tools.entrypoints.cli -> typer` (P-5's guarded import in `cli/__init__.py`) and
  `mapping_suite_sdk.tools.entrypoints.cli.** -> typer`. MongoDB and GitHub need no line: after P-2/P-3
  their libraries are reached only under `TYPE_CHECKING` (excluded) or through `require()`
  (`importlib`, invisible to import-linter); an unmatched ignore line would itself fail the contract.
  The core-only check (P-10) covers the `require()` paths at runtime. The contract is the standing
  regression guard for the developer-tooling scenario "A core module importing an optional library
  fails the gate"; task 4.5 checks it by hand once.
- **P-10 Core-only check in the gate.** `make test-core-only`:
  `rm -rf dist temp/core-only-venv`; `poetry build --format wheel`; create the venv with the Poetry
  environment's interpreter (`$$(poetry env info -e) -m venv temp/core-only-venv`, so it is the same
  Python as the rest of the gate); `temp/core-only-venv/bin/pip install dist/*.whl pytest`; then, from
  inside `temp/`, `core-only-venv/bin/python -I -m pytest -c /dev/null --noconftest
  --import-mode=importlib -p no:cacheprovider --rootdir=.. ../tests/core_only`. `-c /dev/null` drops `pytest.ini`'s
  `pythonpath = .`; `--noconftest` drops `tests/conftest.py` (it imports `mongomock` → `pymongo`);
  `--import-mode=importlib` and **no `__init__.py` in `tests/core_only/`** keep pytest from putting the
  repo root on `sys.path` (`tests/__init__.py` exists) — together they guarantee the tests import the
  installed wheel, not the source tree. Core-only tests assert absence with
  `importlib.util.find_spec(name) is None` (not installed), not with `sys.modules`.
  `pytest.ini` adds `--ignore=tests/core_only` so the normal run skips them. The target is added in
  task 4.4 — **after** the extras (task 4.3); before that the wheel still depends on every library and
  the check could not pass. `check-all` gains it then, CI runs it on 3.10–3.13, and the `ci.yaml`
  "Install the wheel into a fresh venv" step is deleted in the same task (this check installs and
  imports the wheel). Rejected: a separate CI job (two gates).
- **P-11 Extras in `pyproject.toml`.** `[project.optional-dependencies]`: `mongodb = ["pymongo>=4.11,<5"]`,
  `github = ["gitpython>=3.1,<4"]`, `tracing = ["opentelemetry-api>=1.29,<2", "opentelemetry-sdk>=1.29,<2"]`,
  `cli = ["typer>=0.16,<1"]`, `all` = the five specifiers listed **explicitly** (not the self-reference
  `mapping-suite-sdk[...]`, whose support in poetry-core we do not rely on). `make install` runs
  `poetry install --all-groups --all-extras`. Version `2.0.0`.
- **P-12 mypy criterion (developer, 2026-11-08).** A module is *touched* if it appears in
  `git diff --name-only develop...HEAD -- mapping_suite_sdk` at the end of the change (a package's
  `__init__.py` counts as the package). Every touched module listed in `mypy.ini` is removed from it and
  `make typecheck` stays green. Fixes are local: annotate a reassigned variable with the common base
  type (`no-redef`, `assignment`), narrow `Optional` before use (`union-attr`), bind the repository
  `TypeVar` to a protocol/base with `id` (`attr-defined`). No `# type: ignore` is added to a touched
  module unless its error comes from an untouched module, and then with a one-line reason.
- **P-13 Golden MongoDB documents.** Before P-7 deletes `_persist_to_mongodb`, a **one-off script**
  (`temp/capture_mongodb_golden.py`, not committed; its source is pasted in the commit message) loads the
  v3 and v3L test packages through 1.x's `load_mapping_package(..., persist_to_mongodb=True,
  mongo_client=mongomock.MongoClient(), database_name="golden")`, reads back the stored document and
  writes it with `bson.json_util.dumps(doc, sort_keys=True, indent=2)` to
  `tests/test_data/mongodb_golden/{v3,v3L}.json`. The test for "Same document as 1.x" loads them with
  `bson.json_util.loads` and compares with `==`. The files are committed and never regenerated by the
  suite.
- **P-14 TED-SWS issue.** The migration issue text lives in the PR description; it is posted to
  `meaningfy-ws/ted-rdf-conversion-pipeline` only after developer approval (outward-facing).

## Algorithm / approach

Order = risk-down, each step leaves `make check-all` green:

1. Guard helper (P-1).
2. Tracing (P-4), GitHub split (P-3), MongoDB type-hint moves + guards (P-2), CLI guard (P-5): one
   boundary per commit; the existing suite (with extras) proves no behaviour change.
3. Golden documents (P-13), then `save_mapping_package_to_mongodb` (P-7) and the removal of the
   MongoDB parameters from `load_mapping_package` (DEC-1).
4. `convert_mapping_package` (P-6), root exports + logging (P-8, DEC-6), extras (P-11), then the
   core-only check (P-10) — only now can it pass — then the import-linter contract (P-9).
5. Core-only tests for every optional-integrations / public-api scenario.
6. mypy (P-12), docs, CHANGELOG + migration, TED-SWS issue text.

Worked example — a core-only consumer after the change:

```python
# pip install mapping-suite-sdk        (pydantic only)
from mapping_suite_sdk import load_mapping_package, convert_mapping_package, save_mapping_package_to_mongodb
pkg = load_mapping_package(Path("package_v2_folder"))            # v2 → v3L, validated; no pymongo/git/otel imported
full = convert_mapping_package(load_mapping_package(p, include_test_data=True))   # already v3 → same object
save_mapping_package_to_mongodb(pkg, client, "db")
# ImportError: MongoDB support needs: pip install mapping-suite-sdk[mongodb]
```

`tracer.py` shape (P-4):

```python
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
except ImportError:  # the [tracing] extra is not installed: decorators become no-ops
    trace = None
_MSSDK_TRACER_PROVIDER = TracerProvider(...) if trace else None

def traced_routine(func):
    if trace is None:
        return func
    ...  # unchanged
```

Idempotency: no step writes persistent state except `save_mapping_package_to_mongodb`, which upserts
by id (mongodb-persistence "Saving twice updates in place"; 1.x inserted and failed on a repeat). `make test-core-only`
recreates its venv each run (`rm -rf temp/core-only-venv` first), so re-running it is safe.

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| `try: import pymongo except ImportError: pass` at module top in a core module | `TYPE_CHECKING` for hints, `require()` at the call | Silent `None`s turn into `AttributeError`s far from the cause |
| Mock `sys.modules` (or assert on it in the normal suite, where `conftest.py` already imported `pymongo`) to "prove" a library is absent | The core-only venv (P-10), `find_spec(...) is None` | EPIC rabbit-hole: mocking proves nothing about the wheel |
| Change the decorator API of `tracer.py` | Keep `traced_routine` / `traced_class` as they are | 38 importers must not change |
| Keep a 1.x shim for `persist_to_mongodb` | Delete it; DEC-1 | EPIC no-go |
| `logging.basicConfig` anywhere under `mapping_suite_sdk/` except the CLI root callback | Named loggers only | DEC-6 |
| Add `# type: ignore` to pass P-12 | Fix the type locally | The criterion is that touched modules are type-clean |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| A core module still imports an optional library at module level | import-linter contract (P-9) fails in `make check-all`; core-only check fails at import | Move the import under `TYPE_CHECKING` or behind `require()` |
| An integration is reached through `importlib` / a function-level import the linter cannot see | `tests/core_only/` scenario fails in the core-only venv | Add the missing `require()` at that call site |
| Integration called without its extra | `require()` | `ImportError` naming feature + extra (spec) |
| `mssdk` run without `[cli]` | `SystemExit` in the CLI package | One-line message, exit 1, no traceback |
| Circular import from the new root re-exports | `import mapping_suite_sdk` fails in any test | Keep `config` first in the root; services import `mssdk_config` from `mapping_suite_sdk.config` if a cycle appears |
| Saved document differs from 1.x | Golden comparison test (P-13) fails | Fix the save path; never regenerate the golden file to pass |
| `poetry install --all-extras` misses an extra in CI | Existing suite fails on missing `pymongo`/`git` | Fix the extras table (P-11) |
| A touched module still has mypy errors | `make typecheck` after removing it from `mypy.ini` | Fix locally (P-12); if the error is in an untouched module, scoped ignore with a reason |
| TED-SWS breaks on 2.0 | It pins `<2` (EPIC Impact) | Migration issue (P-14) |

## Risks / Trade-offs

- [The core-only check adds ~20–40 s to every `check-all`] → acceptable for one gate; it replaces the
  CI wheel-install step.
- [Root re-exports import most of the package at `import mapping_suite_sdk`] → import cost was already
  paid by consumers that import services; measured once in the PR.
- [P-12 widens as more modules are touched] → errors are local by the baseline count (52 in the
  likely-touched modules); if fixing one needs a change in an untouched core module, that module is
  then touched too and must also be clean — stop and report if that cascades beyond `core/`.
- [Public surface now includes `*.models`] → a model refactor becomes a major; that is the intent
  (TED-SWS builds on them).

## Open Questions

None.
