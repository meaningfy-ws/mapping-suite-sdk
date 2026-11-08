# public-api Specification

## Purpose
What consumers may rely on: the names exported from `mapping_suite_sdk` and from any `*.models` package, the conversion of loaded packages, and a library that leaves application logging alone. `DEC-n` references are the decisions in `openspec/changes/archive/2026-11-08-modular-core/`.
## Requirements
### Requirement: Public API importable from the package root
`mapping_suite_sdk` SHALL export `load_mapping_package`, `validate_mapping_package`,
`convert_mapping_package`, `detect_mapping_package_version`, `load_mapping_suite_from_folder`,
`save_mapping_package_to_mongodb`, the v3 model classes and the typed errors, and importing it SHALL
NOT import any optional library (modular-core DEC-7, DEC-7a). Names exported from the root and from
any `*.models` package are the public API: they SHALL change incompatibly only in a major release;
adapters and services are internal.

#### Scenario: Import the loader from the root
- **WHEN** a core-only consumer runs `from mapping_suite_sdk import load_mapping_package`
- **THEN** the import succeeds
- **AND** `"pymongo" not in sys.modules`

### Requirement: Importing the library leaves logging alone
Importing `mapping_suite_sdk` SHALL NOT change the root logger's level, handlers or format; the
library SHALL log only under the `mapping_suite_sdk` logger (DEC-6).

#### Scenario: Application logging unchanged
- **WHEN** an application configures the root logger at WARNING with one handler and then imports `mapping_suite_sdk`
- **THEN** the root logger still has level WARNING and exactly that handler

#### Scenario: Model modules stay importable by path
- **WHEN** a consumer runs `from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import VersionRange`
- **THEN** the import succeeds on a core-only install

### Requirement: Convert a loaded package to another version
`convert_mapping_package(mapping_package, to_version="v3")` SHALL detect the source version from the
model's type and return the package converted to `to_version` (`"v3"` or `"v3L"`), applying the same
rules as `load_mapping_package` (DEC-7a).

#### Scenario: v2 to v3
- **WHEN** a consumer passes a loaded `MappingPackageV2` to `convert_mapping_package`
- **THEN** it returns a `MappingPackageV3` equal to `convert_mapping_package_model("v2", "v3", package)`

#### Scenario: Same version returns the package unchanged
- **WHEN** a consumer passes a `MappingPackageV3` with `to_version="v3"`
- **THEN** it returns that same object

#### Scenario: Lightweight cannot become full
- **WHEN** a consumer passes a `MappingPackageV3Lightweight` with `to_version="v3"`
- **THEN** it raises `UnsupportedConversionError`

#### Scenario: Not a mapping package
- **WHEN** a consumer passes an object that is not a v1, v2, v3 or v3-lightweight package
- **THEN** it raises `VersionDetectionError`

#### Scenario: Unknown target version
- **WHEN** a consumer passes `to_version="v4"` (or `"v1"` / `"v2"`, which are not conversion targets)
- **THEN** it raises `UnsupportedVersionError`

