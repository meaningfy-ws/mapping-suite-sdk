> Derives from: EPIC `in-memory-package-io` (#95), DEC-1…DEC-5.

## Context

The loaders (v1, v2, v3, v3L and the asset loaders in `core/adapters/loader.py`), the version detector and the
v3 serialiser all take a filesystem `Path`. They use a small part of its API:

| Who | `Path` API used |
|---|---|
| Loaders (read) | `/`, `.name`, `.suffix`, `exists`, `is_file`, `is_dir`, `iterdir`, `glob("*.ttl")`, `relative_to`, `read_text`, `read_bytes`; plus the builtin `open(path, "rb")` in `load_file_by_extensions` |
| Version detector (read) | `exists`, `is_dir`, `glob(pattern)` with patterns such as `test_data/*/*.xml`, `.open(encoding=…)` |
| v3 serialiser (write) | `/`, `.parent`, `mkdir(parents, exist_ok)`, `write_text`, `write_bytes` |

`zipfile.Path` lacks `relative_to`, `suffix` (before 3.11) and `glob` (before 3.12), and cannot be written to. That
settles the rabbit-hole in the EPIC: we add a small adapter rather than restrict the loaders.

## Decisions

- **P-1 — `InMemoryPath`, one adapter for read and write (DEC-2, DEC-3).** A `PurePosixPath` subclass
  in `core/adapters/in_memory_path.py`, backed by a `dict[str, bytes]` of file contents keyed by absolute posix path.
  It implements exactly the API in the table above. A fresh subclass is made per archive so that paths derived with
  `/` share the same dict on Python 3.10–3.13 (the `with_segments` hook only exists from 3.12). `relative_to` returns
  a real `Path`, because asset models validate `path` as `Path`. Spike: `inputs/spike_mempath.py` (3.10 and 3.12).
  Rejected: a `zipfile.Path` wrapper (two read APIs, still no write side); restricting the loaders to the
  `zipfile.Path` subset (touches every loader and still lacks `relative_to`).
- **P-2 — Builtin `open` goes.** `load_file_by_extensions` reads with `file_path.read_bytes()` instead of
  `open(file_path, "rb")`; the behaviour on disk is unchanged.
- **P-3 — Load from bytes shares the pipeline of `load_mapping_package`.** The body of `load_mapping_package`
  after the path checks becomes `_load_and_convert(root, version, …)`; both functions call it. The only difference:
  the bytes variant validates the *loaded source model* before conversion, where the path variant validates the
  folder. Both run the same version validator on the same model.
- **P-4 — Signature.** `load_mapping_package_from_bytes(data, *, target_version="v3", include_output=False,
  validate_package=True)`. `target_version="v3"` loads test data (like `include_test_data=True`), `"v3L"` does not.
  `include_output` mirrors `load_mapping_package` (default off) — an addition to DEC-1 so both loaders agree.
- **P-5 — Hash on export (DEC-1).** `mapping_package_to_zip_bytes`, `save_mapping_package_v3_to_folder` and
  `save_mapping_package_v3_to_archive` all take `update_hash=True`. When true they set
  `package.metadata.mapping_suite_hash_digest` to `MappingPackageV3Hasher(package).hash()` **on the passed
  package**, so the caller holds the hash that was written (documented in the docstrings).
- **P-6 — Wrapping folder (DEC-4).** If every file in the ZIP sits under one top-level folder, that folder is the
  package root; otherwise the ZIP root is. `__MACOSX/` entries (added by macOS Finder) are ignored; found by
  the builder on the shipped v3L test ZIP. The bytes loader's wrapping-folder rule is new: the archive-file loaders
  only unwrap a folder named like the ZIP. Converging them is a follow-up (R-9).
- **P-7 — Placement.** `load_mapping_package_from_bytes` in `tools/services/load_mapping_package.py`; the three
  export functions in a new `mapping_package_v3/services/serialise_mapping_package_v3.py` (mirrors the v2
  module). All four are exported from `mapping_suite_sdk`. No new dependency; works in the core-only install.

## Algorithm / approach

```python
root = InMemoryPath.from_zip(data)               # bytes | BinaryIO -> root path, P-6; bad ZIP -> ValueError
version = detect_mapping_package_version(root)    # unchanged detector, reads through InMemoryPath
package = _load_and_convert(root, version, …)     # unchanged loaders + convert_mapping_package

root = InMemoryPath.empty()
MappingPackageV3Serialiser().serialise(root, package)   # unchanged serialiser, writes into the dict
return root.to_zip()                                    # ZIP_DEFLATED bytes
```

`save_mapping_package_v3_to_archive(package, path)` = `path.write_bytes(mapping_package_to_zip_bytes(package))`;
`save_mapping_package_v3_to_folder(package, path)` = the serialiser on `path`. All operations are pure functions of
their input (re-running gives an equal package; the ZIP bytes may differ, see the EPIC no-gos).

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Extract to a temp dir "just for the bytes path" | `InMemoryPath` | DEC-2: nothing on disk |
| Add `isinstance(path, InMemoryPath)` branches in loaders | Keep loaders path-agnostic | One loader per version |
| Compare ZIP bytes in tests | Compare loaded packages and hashes | No-go: no deterministic ZIP |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Bytes are not a ZIP | `zipfile.BadZipFile` in `from_zip` | `ValueError("Failed to extract ZIP file: …")`, as `ArchiveExtractor` |
| Version cannot be detected | detector returns `None` | `VersionDetectionError` |
| Unsupported version / conversion | `_validate_conversion_path` | `UnsupportedVersionError` / `UnsupportedConversionError` |
| Invalid source or result (hash, structure) | version validator | its typed `MPValidationException` subclass |
| Missing file read inside the ZIP | `InMemoryPath.read_bytes` | `FileNotFoundError`, as on disk |

## Risks / Trade-offs

- [`InMemoryPath` drifts from what a future loader calls] → the round-trip tests load every test-data version
  through it; a new `Path` call fails those tests with `AttributeError`.
- [Whole ZIP held in memory] → accepted by the EPIC (consumer bounds the size).

## Open Questions

None.

## Clarity gate

Self-score 9/10 (lead): every DEC is cited, the API surface is enumerated, the error matrix covers the spec
scenarios; −1 because the `InMemoryPath` subset is proven by tests rather than by type.

## Review decisions (stage 1, five lenses) — to apply before merge

Accepted:
- **R-1 (L1 P1)** `from_zip` rejects entry names that are absolute, contain `\` or have `..` in their parts → `ValueError`; test with `pkg/output/../../x.ttl`.
- **R-2 (L1 P2)** `save_mapping_package_v3_to_folder` serialises into `InMemoryPath.empty()` first, and `write_bytes` rejects `..`, so assets cannot escape the folder.
- **R-3 (L1 P2)** Decompression cap: sum `info.file_size` before reading; above a module constant (1 GiB) → `ValueError`.
- **R-4 (L1 P2)** `from_zip` turns `BadZipFile`, `NotImplementedError`, `RuntimeError`, `EOFError`, `zlib.error` and `OSError` into the bad-archive `ValueError`.
- **R-5 (L1 P3, L4 W2)** The base `InMemoryPath` has no `_files` store; only `from_zip`/`empty` make usable archives.
- **R-6 (L4 W1, L5 P2-3)** `_load_and_convert` loses the flag: `load_mapping_package` validates the folder itself before calling it.
- **R-7 (L5 P2-2, L4 S1)** One `_normalize_target_version` in `convert_mapping_package.py`, used by both callers.
- **R-8 (L2 P2-1/2-2, P3-3)** The spec's "equals" means up to file order within a collection; tests compare the whole model order-insensitively, add the multi-file v2 eForms round trip, and fix the path-vs-bytes test to load the inner folder; the spec shows `*,`.
- **R-9 (L5 P1)** P-6 note: the bytes loader's wrapping-folder rule is new; archive-file loaders only unwrap a folder named like the ZIP. Converging them is a follow-up.
- **R-10 (L3 P3-1)** `InMemoryPath` docstring lists what loaders must not use (`isinstance(Path)`, builtin `open`, `os`/`shutil`, `stat`/`resolve`).

Rejected:
- Rename `mapping_package_to_zip_bytes` (L3, L5): DEC-1 fixes the name from #95.
- `PackagePath` Protocol (L4 S5), constants for `__MACOSX/` (L4 S2), comprehension rewrites (L4 S3), shared ZIP owner (L5 P2-4): follow-ups or not worth the churn.
