from pathlib import Path

from mapping_suite_sdk.core import env_property, DefaultValueConfigResolver


class MPV3AssetsPathsConfig:
    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="metadata.jsonld")
    def MPV3_METADATA_FILE_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="transformation/conceptual_mappings.xlsx")
    def MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="validation/shacl/shacl_result_query.rq")
    def MPV3_SHACL_SHAPES_QUERY_FILE_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="transformation/resources")
    def MPV3_VOCABULARY_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="transformation/mappings")
    def MPV3_TECHNICAL_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="test_data")
    def MPV3_TEST_DATA_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="validation/sparql")
    def MPV3_SPARQL_TEST_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="validation/shacl")
    def MPV3_SHACL_TEST_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)

    @env_property(config_resolver_class=DefaultValueConfigResolver, default_value="output")
    def MPV3_TEST_RESULT_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
        return Path(config_value)
