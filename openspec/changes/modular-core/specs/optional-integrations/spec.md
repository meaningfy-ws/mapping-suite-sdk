## ADDED Requirements

### Requirement: Core works without optional libraries
With only the core installed, loading, validating, converting, hashing and serialising a mapping
package SHALL work, and `pymongo`, `git`, `opentelemetry` and `typer` SHALL NOT be imported
(modular-core DEC-2, DEC-8).

#### Scenario: Core-only round trip
- **WHEN** a consumer has run `pip install mapping-suite-sdk` with no extras
- **AND** it loads a v2 package folder with `load_mapping_package(path)`, converts it to v3 and validates it
- **THEN** it gets a valid `MappingPackageV3`
- **AND** none of `pymongo`, `git`, `opentelemetry`, `typer` is importable in that environment

### Requirement: A missing extra names itself
Calling a feature whose extra is not installed SHALL raise `ImportError` whose message names the
feature and the `pip install mapping-suite-sdk[<extra>]` command (DEC-4).

#### Scenario: MongoDB without its extra
- **WHEN** the core-only consumer calls `save_mapping_package_to_mongodb`
- **THEN** it raises `ImportError` with message containing `pip install mapping-suite-sdk[mongodb]`

#### Scenario: GitHub without its extra
- **WHEN** the core-only consumer calls a `load_mapping_packages_*_from_github` function
- **THEN** it raises `ImportError` with message containing `pip install mapping-suite-sdk[github]`

### Requirement: Tracing is optional
Without the `tracing` extra, traced operations SHALL run unchanged and produce no spans (DEC-5).

#### Scenario: Load without OpenTelemetry
- **WHEN** the core-only consumer loads a package
- **THEN** the call returns the same package as with tracing installed
- **AND** no error or warning about tracing is emitted

### Requirement: The all extra restores full behaviour
`pip install mapping-suite-sdk[all]` SHALL install every optional integration.

#### Scenario: Existing suite on all extras
- **WHEN** the test suite runs in an environment with `mapping-suite-sdk[all]`
- **THEN** it passes
