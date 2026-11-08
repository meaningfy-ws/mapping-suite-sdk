> Derives from: EPIC `modernise-tooling-and-python` ([proposal.md](proposal.md), closes #93)
> Document type: implementation PLAN (design half); pair: [tasks.md](tasks.md).

## Context

Baseline on `develop` @ `ff6a66a`, Python 3.12 (recorded 2026-11-08):

- `pytest tests/unit`: 961 passed, coverage 96.79% (floor 80% in `tox.ini`).
- `lint-imports`: 8 contracts kept, 0 broken.
- Ruff with the target rule set (`E,F,W,I,UP,B,C90`, line length 127): 662 findings — `I001` 173, `UP045` 145, `W293` 90, `UP006` 65, `E501` 113, `E712` 29, `B904` 10,
  `F821` 2 (string forward refs in `_persist_to_mongodb`, removed by `modular-core`); 445 safe fixes
  + 46 unsafe. `C901` passes even at max-complexity 10.
- CI (`code-quality.yaml`): pylint report + PR comment, `make generate-models` + `git diff`
  sync check, `make test-unit` (→ tox → pytest), Codecov — all on Python 3.11 only.
  SonarQube Cloud (free plan) analyses the repo by Automatic Analysis, outside CI (DEC-7).
- Generated modules (by `make generate-models`): `mapping_suite_sdk/mapping_package_v3/models/mapping_package_v3*.py`
  and `mapping_suite_sdk/mapping_suite/models/mapping_suite.py`; it also rewrites `context.jsonld`
  next to each schema. `core/models` and the v1/v2 models are hand-written.
- Makefile pins `poetry==2.0.1` (`install-poetry` target).

Reference style: `../rdf-fingerprinter/` — `ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`,
`pyproject.toml`, `.github/workflows/ci.yml`.

## Goals / Non-Goals

**Goals:** the two capabilities in the spec deltas — `developer-tooling` (one gate) and
`package-distribution` (3.10–3.13, ranged deps).

**Non-Goals:** everything in the EPIC's No-gos.

## Decisions

Settled in the EPIC: DEC-1 (floor 3.10), DEC-2 (drop unused deps), DEC-3 (ranges), DEC-4 (Ruff
replaces pylint/radon/xenon/tox), DEC-5 (root config files), DEC-6 (mypy baseline), DEC-7 (Codecov in CI;
Sonar outside CI), DEC-8 (release 1.1.0).

New, made while planning:

- **P-1 Ruff rule set** = `E,F,W,I,UP,B,C90`, `line-length = 127`, `target-version = "py310"`,
  `max-complexity = 15` (verified: the code passes at 10). `extend-exclude` =
  `["mapping_suite_sdk/mapping_package_v3/models/mapping_package_v3*.py",
  "mapping_suite_sdk/mapping_suite/models/mapping_suite.py"]`; `mypy.ini` excludes the same files.
- **P-2 Lint debt lands in two commits:** (a) `ruff check --fix` + `ruff format` (mechanical, no
  behaviour change, tests prove it); (b) hand fixes of the remaining findings. Findings that need a
  refactor (e.g. `B008` in typer signatures — typer's idiom) get a per-file ignore with a reason.
- **P-3 Dependency groups:** `test` (pytest, pytest-cov, mongomock), `lint` (ruff, mypy,
  import-linter), `model` (linkml). `[dependency-groups]` (PEP 735) needs Poetry ≥2.2, so
  `install-poetry` pins `poetry>=2.2,<3`. `make install` runs `poetry install --all-groups` and
  **no longer runs `poetry lock`** (a gate must not rewrite the lock).
- **P-7 Scripts:** `[tool.poetry.scripts]` moves to `[project.scripts]`
  (`mssdk = "mapping_suite_sdk.tools.entrypoints.cli.mssdk:mssdk_cli_command"`), as in rdf-fingerprinter.
- **P-8 Install proof:** CI builds the wheel (`poetry build`), installs it into a fresh venv with
  `pip`, and runs `python -c "import mapping_suite_sdk"` — this, not `poetry install`, proves the
  package-distribution install scenarios. The rdf-persistence co-resolution is a one-off local
  check recorded in the PR (`uv pip compile` of both on 3.13).
- **P-9 Required checks:** after `ci.yaml` replaces `code-quality.yaml`, update `develop`'s branch
  protection so the required contexts are the four matrix jobs plus `GitGuardian Security Checks`,
  `CodeQL`, `codecov/patch`; drop `Pylint` and `Unit Tests` (they no longer exist).
- **P-10 CI triggers:** `pull_request` (any base) and `push` to `develop`, no paths filter (a
  gate that skips on docs-only PRs cannot be a required check).
- **P-4 Codegen sync check** moves from inline CI shell into `make check-codegen`
  (`generate-models` then `git diff --exit-code -- mapping_suite_sdk resources/schema`), so it is
  part of `check-all` locally too. It first runs `git diff --quiet -- mapping_suite_sdk resources/schema`; on a dirty tree it
  stops with "commit or stash first" before generating. `gen-jsonld-context` runs with
  `--no-metadata` (found while applying): otherwise each `context.jsonld` carries a
  `generation_date` and the check could never pass; the dropped `comments` block is not read by
  any code.
- **P-5 linkml on 3.13:** the `model` group must resolve on 3.10–3.13. If the current
  `linkml>=1.9.2,<1.9.5` cannot, widen it to the lowest version that installs on 3.13 and prove
  `make check-codegen` yields no diff; if a newer generator changes the output, regenerate in its
  own commit.
- **P-6 Ranges** (lower bound = currently locked minor):
  `pydantic>=2.10,<3`, `opentelemetry-api>=1.29,<2`, `opentelemetry-sdk>=1.29,<2`,
  `gitpython>=3.1,<4`, `pymongo>=4.11,<5`, `typer>=0.16,<1`. (Found while applying: `typer`
  0.16 is the first release that accepts Click 8.2; with Click ≥8.2 `mssdk` with no arguments
  exits 2 instead of 0 and errors go to stderr. Developer chose to move to the new Click and
  note the exit code in the CHANGELOG, 2026-11-08.)

## Algorithm / approach

Order = least risk first, each step leaves `make check-all` (or, before it exists, the old
`make test-unit`) green:

1. Add root configs (`ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`) — copies of the
   `tox.ini` sections plus the new tools. Nothing reads them yet except pytest/coverage.
2. Rewrite the Makefile quality section to the new targets; keep `generate-models*`,
   docs targets untouched. `test-unit` becomes an alias of `test`.
3. Normalise `pyproject.toml` (DEC-2/3/5, P-3, P-6), `poetry lock`, delete `tox.ini`, `.pylintrc`,
   `requirements.txt`.
4. Lint debt (P-2), then mypy baseline: fix trivially, otherwise targeted `# type: ignore[code]`
   or a per-module section in `mypy.ini` — no refactors.
5. CI: `ci.yaml` with the matrix and the wheel-install step (P-8); delete `code-quality.yaml` and
   `push-badges-update.yaml` (it maintains the pylint badge).
6. Docs: README Python/dev commands, CHANGELOG 1.1.0, AGENTS.md make targets.

Example — the target Makefile surface:

```make
check-all: lint typecheck check-architecture check-codegen test
lint:          ; poetry run ruff check . && poetry run ruff format --check .
format:        ; poetry run ruff check --fix . && poetry run ruff format .
typecheck:     ; poetry run mypy mapping_suite_sdk
test:          ; poetry run pytest --cov=mapping_suite_sdk --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```

Idempotency: `check-all` is read-only except `check-codegen`, which regenerates the generated
modules and `context.jsonld` files and then fails on any diff; on a clean, in-sync tree it
leaves no change, so re-running the gate is safe. `.coveragerc` keeps an `[xml]` section
(`output = coverage.xml`) for Codecov.

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| Mix `ruff --fix` output with hand edits in one commit | Two commits (P-2) | Reviewable diff; mechanical one needs no reading |
| Refactor code to satisfy a lint rule | Per-file ignore with reason | Appetite; no behaviour change in this EPIC |
| `poetry lock` inside `make install` | Lock only when deps change | A gate must not mutate the lockfile |
| Lint generated modules | `extend-exclude` them | Their style is the generator's |
| Keep `requirements.txt` "for the badge" | Delete with the badge workflow | Dead file |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| A dependency has no 3.10 or 3.13 wheel | CI matrix job fails at `make install` | Lower/raise that range's bound; record in CHANGELOG |
| `linkml` does not install on 3.13 | `model` group install fails on 3.13 job | P-5: widen linkml; if regeneration diff, separate commit |
| `ruff --fix` changes behaviour | Test suite fails after the mechanical commit | Revert that rule's autofix, ignore it with reason |
| mypy baseline has many errors | `make typecheck` red | Per-module `ignore_errors` in `mypy.ini` with a `# shortcut:` note; tightening is later |
| Coverage drops below 80% | `make test` fails | Not expected (no code removed); investigate, don't lower floor |
| Required check never reports (old job name still required) | PR stuck "Expected — waiting" | P-9: update required contexts in the same PR that renames the jobs |

## Risks / Trade-offs

- [3.10 floor keeps `Optional[...]`/`Union` → `UP045` fixes produce `X | None`, valid on 3.10] → fine.
- [Four CI jobs cost more minutes] → acceptable; free tier for public repo.
- [Dropping `click` from deps: a consumer importing `click` via MSSDK breaks] → typer still pulls it; negligible.

## Open Questions

None.
