# Seed: GitHub issue #93 — Support Python 3.13 and move dependency pins to compatible ranges

> Secondary input, preserved verbatim; the EPIC (proposal.md) supersedes it.
> Source: https://github.com/meaningfy-ws/mapping-suite-sdk/issues/93

## Summary
mapping-suite-sdk cannot be installed on Python 3.13: `requires-python = ">=3.10,<3.13"`, and several runtime dependencies are pinned exactly to versions from early 2025. Please support Python 3.13 (and keep 3.12), and move the pins to compatible ranges on current releases.

## Context
- Consumer: Mapping Workbench 2 (`meaningfy-ws/mapping-workbench-v2`). Its API is Python 3.13 (ADR-009) and will import and export mapping packages through MSSDK v3, in-process (MSSDK used as a library).
- It also depends on `rdf-persistence` (Python >=3.12, pydantic 2.14, rdflib 7.6, linkml 1.12 in its generate extra), so MSSDK must resolve in the same environment.
- mapping-suite-sdk commit: `ff6a66a` (develop).

## Current behaviour
`pyproject.toml`:
```toml
requires-python = ">=3.10,<3.13"
dependencies = [
    "pydantic>=2.10.0,<3.0.0",
    "pandas==2.1.4",
    "opentelemetry-api==1.29.0",
    "opentelemetry-sdk==1.29.0",
    "opentelemetry-instrumentation==0.50b0",
    "lxml>=5.3.0,<6.0.0",
    "openpyxl>=3.1.0,<4.0.0",
    "gitpython>=3.1.0,<4.0.0",
    "pymongo>=4.11.0,<5.0.0",
    "typer>=0.15.0,<0.16.0",
    "click>=8.0,<8.2"
]
```
`uv add mapping-suite-sdk` in a Python 3.13 project fails on `requires-python`; `pandas==2.1.4` has no Python 3.13 wheels.

## Expected behaviour
- `requires-python = ">=3.12"` (or `>=3.10` if older consumers still need it), with CI running on 3.12 and 3.13.
- Exact pins replaced by compatible ranges on current releases (e.g. `opentelemetry-*>=1.29,<2`, `click>=8.1`, `typer>=0.15`), so a consumer's resolver can find one set with other libraries.
- `pandas`, `openpyxl` and `lxml` are declared but not imported anywhere under `mapping_suite_sdk/` (`git grep` at `ff6a66a`); remove them unless a planned feature needs them.
- A consumer whose resolver needs a different version than MSSDK's test matrix is not blocked by an exact pin.

## Why it belongs in mapping-suite-sdk
Only MSSDK can change its own metadata. A consumer cannot work around a `requires-python` cap except by downgrading its own Python, and pinning a library to one Airflow deployment's versions forces every other consumer onto them.

## Acceptance
- **Given** a Python 3.13 project, **when** it runs `uv add mapping-suite-sdk`, **then** the install succeeds and `import mapping_suite_sdk` works.
- **Given** the CI matrix, **when** tests run, **then** they pass on 3.12 and 3.13.
- **Given** a project that also depends on `rdf-persistence` from its `develop` branch, **when** it resolves, **then** one compatible set is found.

## Impact on the consumer
Blocks MWB2's MSSDK integration (planned for an iteration after v1); filed now so the fix is ready when that work starts.

