# EPIC: Load and save mapping packages in memory

Closes #95. Depends on `modular-core` (public API surface, DEC-7 there; core without optional libraries).

## Appetite

MEDIUM — one new capability (package I/O over bytes and streams, plus public folder/archive
export) on top of the existing loaders and serialisers; no format change.

## Why

Web consumers (Mapping Workbench 2) receive package ZIPs as HTTP uploads and return exports as
downloads, with files in S3, never on the API's disk. Today loading accepts only a `Path`, and v3
export exists only as an internal adapter that writes a folder — so every consumer writes temp
files and re-implements zipping, which is how MWB1 drifted from the format.

## Solution outline

A consumer passes the bytes (or a binary stream) of a package ZIP of any supported version and gets
back a validated `MappingPackageV3`, with nothing written to disk. It passes a `MappingPackageV3`
built in memory and gets back the bytes of a ZIP whose hash MSSDK computed. Path-based export
(folder, archive) becomes public too, so all four directions are first-class and round-trip.

## Key decisions

- **DEC-1**: New public functions: `load_mapping_package_from_bytes(data: bytes | BinaryIO, *,
  target_version="v3", validate_package=True)`, `mapping_package_to_zip_bytes(package, *,
  update_hash=True) -> bytes`, `save_mapping_package_v3_to_folder(package, path)`,
  `save_mapping_package_v3_to_archive(package, path)`. Names as proposed in #95.
- **DEC-2**: Reading from memory reuses the existing folder loaders by giving them a
  `zipfile.Path` over an in-memory `ZipFile` instead of a filesystem `Path` — one loader per
  version, not a second, ZIP-specific loader. Rejected: extracting to a temporary directory
  (violates "writes nothing to disk").
- **DEC-3**: Writing to memory reuses the v3 serialiser by giving it a writable target that is
  either a folder or an in-memory `ZipFile`. Rejected: serialise to a temp folder then zip it.
- **DEC-4**: The archive accepts exactly one extra wrapping folder, as the path loader does today;
  errors are the same typed errors as the path loaders (version detection, unsupported
  conversion, validation) plus the existing bad-archive error for non-ZIP bytes.
- **DEC-5**: Export covers v3 only; v1/v2 are read-only legacy formats.

## Rabbit-holes

- `zipfile.Path` implements most of the `pathlib.Path` read API but not all (no `stat`, no
  `glob` before 3.12, `rglob` absent on 3.10). The PLAN must list every `Path` method the loaders
  call and either restrict them to the common subset or add a small adapter.
- Hash stability: the ZIP bytes may differ between runs (timestamps); equality is of the loaded
  package and its hash, not of the ZIP bytes.
- Large uploads: bytes in memory are bounded by the consumer, not MSSDK; do not add streaming
  decompression to disk.

## No-gos

- No S3 or HTTP clients — the consumer moves bytes.
- No v1/v2 export.
- No new archive formats (tar, 7z).
- No change to the hash algorithm or package layout.
- No deterministic-ZIP guarantee (byte-identical archives).

---

## What Changes

- New public load-from-bytes and save-to-bytes/folder/archive functions, exported from `mapping_suite_sdk`.
- Folder loaders and the v3 serialiser accept a `zipfile.Path` / in-memory ZIP target.
- Docs: `serialisation.adoc` and `quick-start.adoc` gain in-memory examples.

## Capabilities

### New Capabilities
- `in-memory-package-io`: loading packages from bytes/streams and serialising v3 packages to bytes, folders and archives.

### Modified Capabilities

## Impact

- MWB2: drops temp-file handling and the use of the internal serialiser.
- TED-SWS: unaffected (additive).
- Minor release on top of 2.0.0 (2.1.0).
