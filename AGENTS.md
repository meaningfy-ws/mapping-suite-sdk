<!-- meaningfy-template-version: 3.0.0 -->
<!-- CANONICAL, CLI-agnostic agent instruction file (opencode reads AGENTS.md natively; Claude Code
     reads it through the @AGENTS.md import in CLAUDE.md). Edit THIS file. CLAUDE.md is a thin
     pointer that adds only Claude-specific guidance — never a symlink, never a copy. This file
     ROUTES to skills and to the global standard; it never restates that standard (DEC-12 —
     global vs repo split). -->

# Project: Mapping Suite SDK (MSSDK)

Meaningfy project. Build clean, layered, well-tested code; minimise WTFs-per-minute. The
company-wide standard (Clean Code, Clean Architecture, testing, tooling) lives in your **global
agent instructions** (`~/.claude/CLAUDE.md` on Claude Code, `~/.config/opencode/AGENTS.md` on
opencode) — this file does **not** repeat it; it ROUTES to it and to the
installed skills, and records only what is specific to **this** repo.

## Skill routing (use the skill for the task)

- Structuring Python code (domain/adapters/services/entrypoints, SOLID, CI) → **cosmic-python**
- Keeping code minimal — YAGNI, avoid over-engineering, simplest working approach → **ponytail**
  (`/ponytail` to set intensity; `/ponytail-review` for a delete-list on the diff)
- System / solution design (C4, ADRs, contracts) → **architecture**
- Modelling the domain / generating code from a model (`make generate-models`) → **conceptual-modelling**
  (product repos only)
- Any new feature or non-trivial change → start by exploring options (**superpowers:brainstorming**)
- Any feature or bugfix implementation → **superpowers:test-driven-development** (tests first)
- Debugging → **superpowers:systematic-debugging**
- Shaping an EPIC + deriving its PLAN → **epic-planning** + the opsx workflow commands
  (`/opsx:*` on Claude Code, `opsx-*` on opencode)
- Spec readiness (the PLAN clarity gate, ≥9/10) → **clarity-gate**
- BDD features → **bdd-gherkin**
- Commits / branches / PRs → **meaningfy-git-workflow** (mechanics via **commit-commands**)
- Pre-PR review → **meaningfy-code-review** (+ external **code-review**)
- Deploy / release / versioned image (deployable repos) → **ci-cd-delivery**
- Docs → **technical-writing**

If a request conflicts with these, flag it before proceeding.

## The spine — where work is shaped and remembered

This repo carries the Meaningfy **spine** under `openspec/` (OpenSpec, schema `meaningfy`):

- **EPIC ≡ `openspec/changes/<id>/proposal.md`** (the Shape-Up work shape: appetite, why, solution,
  key decisions, rabbit-holes, no-gos).
- **PLAN ≡ `openspec/changes/<id>/design.md` + `tasks.md`** (the clarity gate scores the pair ≥9/10).
- **Normative requirements ≡ `openspec/changes/<id>/specs/<cap>/spec.md`** (RFC-2119 SHALL +
  Given/When/Then; no EARS). They merge into **`openspec/specs/`** — the durable truth — on archive.
- **Seed inputs** (briefs, notes) live in `openspec/changes/<id>/inputs/` — preserved, never groomed.
- **Orientation** is `openspec/config.yaml`'s `context:` field (the native index) — **not** a
  hand-curated MEMORY.md. The truth is `openspec/specs/`.

Drive it with the opsx workflow commands (`/opsx:*` on Claude Code, `opsx-*` on opencode): `propose`,
`explore`, `apply`, `sync`, `archive` — core profile.

**External method skills land in the spine (binding).** `superpowers` provides *disciplines*, not a
parallel spec system — its artifacts MUST land in `openspec/changes/<id>/`, never a `docs/superpowers/`
tree. A **brainstorming** design feeds the **EPIC** (`proposal.md`); **writing-plans is SUPERSEDED** by
the **PLAN** (`design.md`+`tasks.md`); execution uses superpowers TDD, tracked via the opsx `apply`
command.

**Golden thread (cite your parent).** Each artifact cites the one above it: the PLAN (`tasks.md`)
cites its EPIC id on the first line; specs cite their capability; commits reference the change. This
is how any commit traces up to the requirement that justifies it.

## Implementation loop (orchestration)

Before editing a symbol, run gitnexus impact (status → analyze → impact/context); stop and
report HIGH/CRITICAL risk. Loop: generate (tests first) → verify (run tests) → integrate
(present, get consent). On a design-level failure, fix the spec, not the code (Rule of
Divergence). Commit only on explicit developer consent.

## Working conventions

- The innermost layer is **`models`** (per package format: `core/models`, `mapping_package_vN/models`, `mapping_suite/models`). Direction:
  `entrypoints → services → models`, `adapters → models`. `models` imports nothing upward.
  Enforced by `.importlinter`; checked via `make check-architecture`.
- Run Python tooling through Poetry (`poetry run pytest`, …) or, better, the `make` targets below.
- **Subagents** — before spawning one, follow *Subagent dispatch* in the `guardrails` skill: spawn
  only when it pays, brief it fresh, take the base report back, and have finished work checked by a
  second subagent.
- **Subagents share this checkout and branch.** Implementers run one after another; the leader
  commits after each task. Run writers in parallel only on tasks with disjoint files, and they
  never stage or commit. Read-only agents (reviewers, Explore) may run in parallel freely. Use a
  separate worktree (`isolation: "worktree"`) only for overlapping parallel work or when another
  session holds this checkout.
- **Run checks through make** (`make test-unit`, `make all-quality-checks`; `make check-all` once `modernise-tooling` lands); don't hand-roll pytest pipelines.
- **Temporary files** go in `temp/` (git-ignored), not `/tmp` or the session scratchpad.
- **Branches:** `develop` is the default and integration branch (the PR target). Branch off it
  (`feature/…`, `fix/…`, `chore/…`); never commit to it directly. Releases are `X.Y.Z` tags
  (`release-tag-pypi-publish.yaml`).

## `.claude/` is a regenerable index — the truth is `openspec/specs/`

`.claude/` holds the project-scoped Claude Code commands and skills (`/opsx:*`, gitnexus). It is
**not** authority — if anything there disagrees with `openspec/specs/`, `specs/` wins. Do not
create parallel epic/plan files under `.claude/` or `docs/superpowers/`.

## Project specifics

- **Archetype:** library (PyPI `mapping-suite-sdk`, console script `mssdk`).
- **Top-level package:** `mapping_suite_sdk/` (no `/src`); `resources/` ships LinkML schemas and
  generator templates.
- **Modules:** `core/` (shared models; adapters: extractor, loader, serialiser, repository,
  tracer, version detection); `mapping_package_v1/`, `mapping_package_v2/`, `mapping_package_v3/`
  (incl. lightweight) and `mapping_suite/`, each `models/ adapters/ services/`;
  `tools/services/` (version-agnostic load, convert vN→v3, validate) and
  `tools/entrypoints/cli/` (`mssdk`, typer). Public API is re-exported from
  `mapping_suite_sdk/__init__.py`.
- **Domain model:** v3 and mapping-suite models are **generated** from LinkML
  (`resources/schema/**.yaml` → `make generate-models`, templates in `resources/templates/`).
  Never hand-edit a generated module; change the schema and regenerate. CI fails on drift.
- **External systems:** MongoDB (persistence; tests use `mongomock`), GitHub (package extraction
  via gitpython), OpenTelemetry (tracing).
- **Consumers:** TED-SWS (Airflow pipeline) and Mapping Workbench 2 (in-process import/export).
  Public API changes are breaking for them — call them out in the EPIC.
- **Deployable?** no — released as a Python package.
- **Make targets:** `make install`, `make test-unit` (regenerates models, runs tox → pytest +
  coverage ≥80%), `make lint` (pylint), `make check-architecture` (import-linter),
  `make check-clean-code` (radon/xenon), `make all-quality-checks`, `make generate-models`,
  `make build-docs`. Tooling is pre-modernisation; the `modernise-tooling` change aligns it
  (Ruff, mypy, `make check-all`).
- **Commit messages give the why and the what.** Subject: Conventional Commit, imperative, no
  trailing period. Body: **Why** first, then **What** (one bullet per concern), then **Trace**
  (`Refs: <change-id>`, `Closes #<issue>`).
- **GitNexus repo name:** mapping-suite-sdk
