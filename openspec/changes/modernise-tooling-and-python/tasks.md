> Derives from: EPIC `modernise-tooling-and-python` ([proposal.md](proposal.md), closes #93)
> Document type: implementation PLAN (tasks half); pair: [design.md](design.md). Specs: [specs/developer-tooling/spec.md](specs/developer-tooling/spec.md), [specs/package-distribution/spec.md](specs/package-distribution/spec.md).

## 1. Root tool configs

- [x] 1.1 Add `pytest.ini` and `.coveragerc` (from the `tox.ini` sections; floor 80%; `[xml] output = coverage.xml`); `poetry run pytest` still passes (developer-tooling: One quality gate)
- [x] 1.2 Add `ruff.toml` and `mypy.ini` with the P-1 rule set and exclusion globs, mypy as DEC-6 baseline (developer-tooling: Tool configuration in dedicated root files)

## 2. Makefile gate

- [x] 2.1 Replace pylint/radon/xenon/tox targets with `install`, `lint`, `format`, `typecheck`, `check-architecture`, `check-codegen` (P-4), `test` (with xml report), `check-all`; `test-unit` aliases `test`; `install` no longer locks; `install-poetry` pins `poetry>=2.2,<3` (P-3)

## 3. Package metadata

- [x] 3.1 Normalise `pyproject.toml`: `requires-python >=3.10,<3.14`, trimmed ranged deps (DEC-2, P-6), `[dependency-groups]` (P-3), `[project.scripts]` (P-7), classifiers 3.10–3.13, version 1.1.0, `[tool.poetry]` the only tool table (package-distribution: both requirements)
- [x] 3.2 Resolve `linkml` for 3.13 (P-5); `poetry lock`; delete `tox.ini`, `.pylintrc`, `requirements.txt`
- [x] 3.3 Add `tests/unit/test_package_metadata.py`: every runtime dependency is imported under `mapping_suite_sdk/` (distribution→import map: `gitpython`→`git`, `opentelemetry-api`/`opentelemetry-sdk`→`opentelemetry`, `pymongo`→`pymongo`, `pydantic`→`pydantic`, `typer`→`typer`), none uses `==`, each has an upper bound (package-distribution: No unused runtime dependency, No exact pin)

## 4. Lint and type debt

- [x] 4.1 Mechanical commit: `ruff check --fix` + `ruff format`; tests green (P-2a)
- [x] 4.2 Hand-fix or justify-ignore remaining Ruff findings; `make lint` green (P-2b)
- [x] 4.3 mypy baseline green (`make typecheck`), ignores scoped and commented
- [x] 4.4 `make check-all` green on 3.10 and 3.13 locally (developer-tooling: Gate passes on a clean checkout; lint/codegen/coverage failure scenarios checked by hand once and noted in the PR)

## 5. CI

- [x] 5.1 `.github/workflows/ci.yaml`: triggers per P-10; matrix 3.10–3.13 → `make install && make check-all`; wheel-install step per P-8 on every matrix job; Codecov upload on 3.12 only, no Sonar step (DEC-7); delete `code-quality.yaml` and `push-badges-update.yaml` (developer-tooling: CI runs the same gate; package-distribution: Install on Python 3.13 / 3.10)
- [x] 5.2 One-off: on 3.13, `uv pip compile` a requirements file naming `mapping-suite-sdk` (this branch) and `rdf-persistence @ git+https://github.com/meaningfy-ws/rdf-persistence.git@develop`; paste the result in the PR (package-distribution: Resolves next to rdf-persistence)
- [x] 5.3 Update `develop` required status checks to the new job names (P-9)

## 6. Docs and release notes

- [x] 6.1 README (Python support, dev commands, drop pylint badge), `CHANGELOG.md` 1.1.0, AGENTS.md make targets; comment on #93 with the result

## Roadmap

- [x] 1.1 · [x] 1.2 · [x] 2.1 · [x] 3.1 · [x] 3.2 · [x] 3.3 · [x] 4.1 · [x] 4.2 · [x] 4.3 · [x] 4.4 · [x] 5.1 · [x] 5.2 · [x] 5.3 · [x] 6.1

## Verification

`make check-all` green locally on 3.10 and 3.13 and in the CI matrix; wheel installs on every matrix Python; `openspec validate modernise-tooling-and-python --strict`; clarity gate ≥9/10 on design.md + tasks.md.
