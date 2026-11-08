# EPIC: Modernise tooling and support Python 3.10–3.13

Closes #93.

## Appetite

MEDIUM — one new capability (a single `make check-all` gate run on a Python matrix) and the
metadata change it proves; the package code is touched only where the new linters demand it.

## Why

MSSDK cannot be installed on Python 3.13 (`requires-python <3.13`, `pandas==2.1.4` has no 3.13
wheels), which blocks Mapping Workbench 2. Its exact pins force every consumer onto one Airflow
deployment's versions. The developer tooling (tox, pylint, radon/xenon, config inside `tox.ini`,
CI on Python 3.11 only) differs from the Meaningfy standard its sibling `rdf-fingerprinter` follows,
so an agent or developer cannot run one gate locally and trust that CI runs the same one.

## Solution outline

A consumer on any Python from 3.10 to 3.13 can install MSSDK next to other current libraries, and
one command — `make check-all` — is the gate a developer runs locally and CI runs on every PR, on
every supported Python.

- Package metadata: Python `>=3.10,<3.14`; runtime dependencies are only what the code imports,
  as compatible ranges.
- Tooling: Ruff (lint + format), mypy (baseline), import-linter, pytest + coverage ≥80%, each
  configured in its own root file; the Makefile is the only task runner.
- CI: one workflow calls `make check-all` on 3.10–3.13 and keeps the LinkML codegen-sync check.

## Key decisions

- **DEC-1**: Python floor **3.10**, CI on 3.10, 3.11, 3.12, 3.13 — TED-SWS (Airflow) still needs
  3.10; rejected: floor 3.12 like the siblings (would strand TED-SWS).
- **DEC-2**: Drop `pandas`, `lxml`, `openpyxl`, `opentelemetry-instrumentation` and `click` from
  runtime dependencies — nothing under `mapping_suite_sdk/` imports them (`click` arrives through
  `typer`); rejected: keeping them "for later" (YAGNI, `pandas==2.1.4` blocks 3.13).
- **DEC-3**: Runtime pins become ranges bounded by the next major (`>=X.Y,<X+1`); `typer`
  (0.x) bounded `<1`. Rejected: exact pins (block consumers' resolvers).
- **DEC-4**: Ruff replaces pylint; radon/xenon and tox are removed. Ruff's `C90` (mccabe) rule
  keeps the complexity ceiling. Rejected: keeping xenon as a second complexity tool.
- **DEC-5**: Tool configuration lives in dedicated root files (`ruff.toml`, `mypy.ini`,
  `pytest.ini`, `.coveragerc`, `.importlinter`); `pyproject.toml` keeps only `[project]`,
  `[dependency-groups]`, `[tool.poetry]`, `[build-system]`. Rejected: `[tool.*]` in pyproject,
  config in `tox.ini`.
- **DEC-6**: mypy starts as a non-strict baseline (as in rdf-fingerprinter); tightening is a later
  change. Rejected: strict now (would swallow the appetite).
- **DEC-7**: Keep SonarCloud and Codecov upload in CI (one Python only); the pylint PR-comment
  bot and the static pylint badge are removed.
- **DEC-8**: Release stays a patch-compatible minor: **1.1.0** (no API change; dropping
  undeclared-use dependencies is not breaking for importers of MSSDK).

## Rabbit-holes

- Ruff will report lint debt on the existing code. Fix only what is auto-fixable or trivial;
  anything structural gets a per-file ignore with a `# shortcut:` comment, not a refactor.
- Generated LinkML modules: exclude them from Ruff/mypy rather than fight the generator's style.
- `linkml` (dev group) pins a narrow range; it must still resolve on 3.13 — check before
  widening anything else.

## No-gos

- No package layout changes (no moving modules, no renaming layers).
- No public API change — that is `modular-core` (#94) and `in-memory-package-io` (#95).
- No strict mypy, no mutation testing, no pytest-bdd migration of existing tests.
- No release-please or Trusted Publishing migration (the token-based publish workflow stays).
- No Antora restructuring.

---

## What Changes

- `pyproject.toml`: `requires-python = ">=3.10,<3.14"`; dependencies trimmed and ranged; dev tools
  moved to `[dependency-groups]` (`test`, `lint`, `model`); classifiers for 3.10–3.13; version 1.1.0.
- New root configs: `ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`.
- Removed: `tox.ini`, `.pylintrc`, `requirements.txt` (badge stub), radon/xenon targets, pylint targets.
- `Makefile`: `install`, `lint`, `format`, `typecheck`, `check-architecture`, `test`,
  `check-codegen`, `check-all`; `test-unit` kept as an alias of `test`.
- `.github/workflows/ci.yaml` replaces `code-quality.yaml`: matrix 3.10–3.13 running `make check-all`.
- `README.md`: Python support and development commands; pylint badge removed.
- `CHANGELOG.md` created with the 1.1.0 entry.

## Capabilities

### New Capabilities
- `developer-tooling`: the single quality gate (`make check-all`) and what it checks, locally and in CI.
- `package-distribution`: supported Python versions and how runtime dependencies are declared.

### Modified Capabilities

## Impact

- Consumers: TED-SWS unaffected (same API, wider ranges); MWB2 unblocked on 3.13.
- Developers: `make check-all` replaces `make all-quality-checks` / `poetry run tox`.
- CI: four Python jobs instead of one; SonarCloud keeps its token.
