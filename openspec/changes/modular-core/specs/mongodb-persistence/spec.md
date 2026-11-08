## ADDED Requirements

### Requirement: Loading never persists
`load_mapping_package` SHALL NOT accept MongoDB parameters and SHALL NOT write to any store
(modular-core DEC-1).

#### Scenario: Old parameter rejected
- **WHEN** a caller passes `persist_to_mongodb=True` to `load_mapping_package`
- **THEN** it raises `TypeError` for the unexpected keyword

### Requirement: Save a loaded package to MongoDB
`save_mapping_package_to_mongodb(package, mongo_client, database_name, collection_name="mapping_package")`
SHALL store a v3 or v3-lightweight package with the same document shape the 1.x
`persist_to_mongodb=True` path produced (DEC-3).

#### Scenario: Same document as 1.x
- **WHEN** a v3 package is loaded and passed to `save_mapping_package_to_mongodb` with a mongomock client
- **THEN** the stored document equals the one 1.x stored for the same package with `persist_to_mongodb=True`

#### Scenario: Saving twice updates in place
- **WHEN** the same package is saved twice to the same collection
- **THEN** the collection holds one document for that package
