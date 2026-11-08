## ADDED Requirements

### Requirement: Public API importable from the package root
`mapping_suite_sdk` SHALL export `load_mapping_package`, `validate_mapping_package`,
`convert_mapping_package`, `save_mapping_package_to_mongodb`, the v3 model classes and the typed
errors, and importing it SHALL NOT import any optional library (modular-core DEC-7).

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
