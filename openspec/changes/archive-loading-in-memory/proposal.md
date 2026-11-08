# EPIC: Load archive files in memory

Closes #113. Split from #109 (its path bug is fixed in #112). Builds on `in-memory-package-io`
(`InMemoryPath.from_zip`).

Status: shaped, not planned. Parked by the developer on 2026-11-08 ("drop that part for now"):
the current loaders work; derive the PLAN only when this is picked up.

## Appetite

SMALL — five load services and four validate-from-archive services switch from temporary
extraction to the in-memory path MSSDK already has. No format change.

## Why

Two ways of opening an archive coexist. The `*_from_archive` loaders extract the ZIP to a
temporary directory with `ArchiveExtractor` and unwrap only a top-level folder named like the
ZIP. `load_mapping_package_from_bytes` reads the ZIP in memory with `InMemoryPath.from_zip` and
unwraps any single top-level folder. A package archive renamed after it was zipped therefore
loads from bytes but not from its path. Two code paths also mean two places for wrapper bugs
like #109.

## Solution outline

A consumer passing an archive path gets the same package as passing that archive's bytes: the
archive loaders read the file and hand it to `InMemoryPath.from_zip`, then to the existing folder
loaders. Nothing is written to disk on load.

## Key decisions (open — settle in the PLAN)

- **DEC-1**: Fate of the public `archive_unpacker` parameter on `load_mapping_package_v{1,2,3}_from_archive`,
  `load_mapping_package_v3_lightweight_from_archive`, `load_mapping_suite_from_archive` and the
  `validate_*_from_archive` services. Options: (a) remove it — breaking, next major;
  (b) keep it, ignore it and emit a `DeprecationWarning` — minor release, removal at the next major.
  Leaning (b).
- **DEC-2**: One wrapper rule everywhere: the one `from_zip` already applies (any single
  top-level folder).

## Rabbit-holes

- Folder loaders rebase onto a nested `<name>/<name>/` folder; with an in-memory root that
  rebase must not double-apply.
- `__MACOSX/` and `.DS_Store` entries in real archives (the v3L fixture has them) must not count
  as a second top-level folder.
- Every path a loaded asset carries must stay relative to the package root (regression test
  from #112).

## No-gos

- No change to the serialisers' use of `ArchiveExtractor` (writing archives).
- No change to the GitHub extractor (it clones; temporary folders stay).
- No new archive formats.

---

## What Changes

- Archive load and validate services read archives through `InMemoryPath.from_zip`.
- `archive_unpacker` on those services is deprecated or removed (DEC-1).

## Capabilities

### New Capabilities

### Modified Capabilities
- `in-memory-package-io`: path-based archive loading shares the in-memory read path.

## Impact

- TED-SWS and Mapping Workbench 2: affected only if they pass `archive_unpacker` (DEC-1).
- Minor release under DEC-1 (b); major under (a).
