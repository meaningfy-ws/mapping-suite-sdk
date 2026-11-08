> Derives from: EPIC `in-memory-package-io` (#95). One stage, one PR.

## 1. Read from memory

- [x] 1.1 `core/adapters/in_memory_path.py`: `InMemoryPath` with the read API of design §Context, `from_zip` (P-1, P-6); unit tests incl. 3.10-safe `/` derivation and `glob` patterns
- [x] 1.2 `load_file_by_extensions` reads via `read_bytes` (P-2)
- [x] 1.3 `load_mapping_package_from_bytes` + shared `_load_and_convert` (P-3, P-4); tests for every scenario of *Load a package from bytes or a stream*, over v1, v2, v3 and v3L test data

## 2. Write to memory and to disk

- [ ] 2.1 `InMemoryPath` write side: `mkdir`, `write_text`, `write_bytes`, `to_zip`, `empty` (P-1)
- [ ] 2.2 `serialise_mapping_package_v3.py`: `mapping_package_to_zip_bytes`, `save_mapping_package_v3_to_folder`, `save_mapping_package_v3_to_archive` (P-5, P-7); round-trip tests for both requirements

## 3. Publish

- [ ] 3.1 Export the four functions from `mapping_suite_sdk` (`__all__`, `test_public_api.py`); core-only test calls the bytes round trip
- [ ] 3.2 Docs: `serialisation.adoc`, `quick-start.adoc`; CHANGELOG `[2.1.0] - Unreleased`; version 2.1.0

## Roadmap

- [x] 1.1 · [x] 1.2 · [x] 1.3 · [ ] 2.1 · [ ] 2.2 · [ ] 3.1 · [ ] 3.2

## Verification

`make check-all` green (incl. `test-core-only`); MEDIUM: five review lenses + one checker before merge.
