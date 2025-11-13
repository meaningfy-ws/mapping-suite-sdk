from pathlib import Path

from mapping_suite_sdk.core.adapters.config_resolver import env_property, DefaultValueConfigResolver


class MPV1AssetsPathsConfig:
    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="metadata.json")
    def MPV1_METADATA_FILE_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="transformation/conceptual_mappings.xlsx")
    def MPV1_CONCEPTUAL_MAPPING_FILE_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="validation/shacl/shacl_result_query.rq")
    def MPV1_SHACL_SHAPES_QUERY_FILE_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="transformation/resources")
    def MPV1_VOCABULARY_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="transformation/mappings")
    def MPV1_TECHNICAL_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="test_data")
    def MPV1_TEST_DATA_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="validation/sparql")
    def MPV1_SPARQL_TEST_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="validation/shacl")
    def MPV1_SHACL_TEST_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="output")
    def MPV1_TEST_RESULT_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)
