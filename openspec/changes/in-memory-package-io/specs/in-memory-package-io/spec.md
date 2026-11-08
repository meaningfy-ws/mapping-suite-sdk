## ADDED Requirements

### Requirement: Load a package from bytes or a stream
`load_mapping_package_from_bytes(data, *, target_version="v3", include_output=False, validate_package=True)` SHALL accept
the bytes or a binary stream of a package ZIP of any supported version, detect its version,
convert it to v3, validate it, and SHALL write nothing to disk (in-memory-package-io DEC-1, DEC-2).

#### Scenario: v2 ZIP bytes to v3
- **WHEN** `load_mapping_package_from_bytes(data, target_version="v3")` runs on the bytes of a v2 package ZIP
- **THEN** it returns a valid `MappingPackageV3`
- **AND** no file or directory is created on disk

#### Scenario: Binary stream input
- **WHEN** the same ZIP is passed as an `io.BytesIO` stream
- **THEN** the returned package equals the one loaded from the bytes

#### Scenario: One wrapping folder
- **WHEN** the ZIP contains the package inside one top-level folder
- **THEN** it loads the same as a ZIP with the package at its root

#### Scenario: Not a ZIP
- **WHEN** the bytes are not a ZIP archive
- **THEN** it raises the same typed error the archive path loader raises for a bad archive

#### Scenario: Unsafe or oversized archive
- **WHEN** a ZIP entry name is absolute, contains `..` or a backslash, or the entries add up to more than 1 GiB uncompressed
- **THEN** it raises the same typed error as for a bad archive, and nothing is read into the package

#### Scenario: Unknown version
- **WHEN** the ZIP holds a folder whose version cannot be detected
- **THEN** it raises the same version-detection error as `load_mapping_package`

### Requirement: Serialise a v3 package to ZIP bytes
`mapping_package_to_zip_bytes(package, *, update_hash=True)` SHALL return the bytes of a package ZIP
and, when `update_hash` is true, SHALL set the package hash computed by MSSDK (DEC-1, DEC-3).

#### Scenario: Round trip through bytes
- **WHEN** a `MappingPackageV3` built in memory is serialised with `mapping_package_to_zip_bytes(package, update_hash=True)`
- **AND** the bytes are loaded back with `load_mapping_package_from_bytes`
- **THEN** the loaded package equals the original, ignoring file order within a collection
- **AND** its hash validates

### Requirement: Save a v3 package to a folder or an archive
`save_mapping_package_v3_to_folder(package, path, *, update_hash=True)` and
`save_mapping_package_v3_to_archive(package, path, *, update_hash=True)` SHALL write a package that `load_mapping_package` loads back with an equal model (equal ignoring file order within a collection) (DEC-1, DEC-5).

#### Scenario: Round trip through an archive
- **WHEN** a v3 package is saved with `save_mapping_package_v3_to_archive` and loaded with `load_mapping_package`
- **THEN** the loaded package equals the original, ignoring file order within a collection

#### Scenario: Round trip through a folder
- **WHEN** a v3 package is saved with `save_mapping_package_v3_to_folder` and loaded with `load_mapping_package`
- **THEN** the loaded package equals the original, ignoring file order within a collection
