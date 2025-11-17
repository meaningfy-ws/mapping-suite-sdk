from pathlib import Path

from mapping_suite_sdk.core.adapters.config_resolver import env_property, DefaultValueConfigResolver


class MappingSuiteAssetsPathsConfig:
    """Configuration for mapping suite asset paths.

    Defines conventional path fragments for mapping suite components,
    allowing easy configuration and evolution of the suite structure.
    """

    @env_property(config_resolver_class=DefaultValueConfigResolver,
                  default_value="config/mapping_suite_config.json")
    def MAPPING_SUITE_CONFIG_FILE_ASSET_PATH(self, config_value: str) -> Path:
        """Path to the mapping suite configuration file."""
        return Path(config_value)

    # @env_property(config_resolver_class=DefaultValueConfigResolver,
    #               default_value="resources")
    # def MAPPING_SUITE_RESOURCES_COLLECTION_ASSET_PATH(self, config_value: str) -> Path:
    #     """Path to the resources collection directory."""
    #     return Path(config_value)
