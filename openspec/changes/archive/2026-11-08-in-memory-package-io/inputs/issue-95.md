# Seed: GitHub issue #95 — Load and save mapping packages from and to memory (bytes, streams, in-memory ZIP)

> Secondary input, preserved verbatim; the EPIC (proposal.md) supersedes it.
> Source: https://github.com/meaningfy-ws/mapping-suite-sdk/issues/95

## Summary
Load and save mapping packages from and to memory, not only from and to paths: load a package from bytes or a binary stream (a ZIP, with version detection and conversion), and serialise a `MappingPackageV3` to an in-memory ZIP (bytes) with its hash computed. Today loading takes only a `Path`, and there is no public service that writes a v3 package to a folder or an archive (the v3 save services write to MongoDB only; `MappingPackageV3Serialiser` is an adapter that writes a folder).

## Context
- Consumer: Mapping Workbench 2, a web application. A user uploads a package ZIP over HTTP (bytes in memory) and downloads an exported package (bytes streamed back); its files live in an S3 object store, never on the API's disk.
- Today the consumer must write each upload to a temporary file and folder, call MSSDK, and clean up; for export it must use an internal adapter to write a folder, then zip it itself.
- mapping-suite-sdk commit: `ff6a66a` (develop).

## Current behaviour
```python
load_mapping_package(package_folder_path: Path, *, version=None, ...)       # path only
load_mapping_package_v3_from_archive(mapping_package_archive_path: Path, ...) # path only
save_mapping_package_v3_to_mongo_db(...)                                       # MongoDB only
MappingPackageV3Serialiser().serialise(package_folder_path: Path, asset)       # adapter, folder only
```

## Proposed capability
```python
from mapping_suite_sdk import load_mapping_package_from_bytes, mapping_package_to_zip_bytes

# import: version detected, converted to v3, validated, all in memory
package: MappingPackageV3 = load_mapping_package_from_bytes(
    upload_bytes,                    # or a binary stream (typing.BinaryIO)
    target_version="v3",
    validate_package=True,
)

# export: build the package object from the application's data, then serialise
package = MappingPackageV3(metadata=..., technical_mapping_suite=..., ...)
data: bytes = mapping_package_to_zip_bytes(package, update_hash=True)   # the hash computed by MSSDK
```
- Also public, path-based counterparts for export: `save_mapping_package_v3_to_folder(package, path)` and `..._to_archive(package, path)`.
- The archive accepts one extra wrapping folder on input, as the path loader does today.
- Errors are the same typed errors as the path loaders (version detection, unsupported conversion, validation).

## Why it belongs in mapping-suite-sdk
The package format, its archive layout and the hash are MSSDK's; a consumer that zips or unzips packages itself re-implements half the format and can drift from it (MWB1 did). Every web or service consumer needs in-memory I/O, not only MWB2.

## Acceptance
- **Given** the bytes of a v2 package ZIP, **when** `load_mapping_package_from_bytes(data, target_version="v3")` runs, **then** it returns a valid `MappingPackageV3` and writes nothing to disk.
- **Given** a `MappingPackageV3` built in memory, **when** `mapping_package_to_zip_bytes(package, update_hash=True)` runs, **then** loading the bytes back yields an equal package whose hash validates.
- **Given** a path-based round trip (`save_mapping_package_v3_to_archive` then `load_mapping_package`), **then** it yields an equal package.

## Impact on the consumer
Not blocking (temporary files work), but it removes temp-file handling and the use of an internal adapter from MWB2's import and export.

