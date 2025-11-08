from pathlib import Path

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.loader import MappingPackageLoader, TechnicalMappingSuiteLoader, \
    VocabularyMappingSuiteLoader
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mp_v3_lightweight.adapters.mp_v3_lightweight_loader import MappingPackageV3LightweightMetadataLoader
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


@traced_class
class MappingPackageV3LightweightLoader(MappingPackageLoader):
    """Main loader for complete mapping packages.

    Coordinates the loading of all components of a mapping package using specialized loaders.
    """

    def __init__(self,
                 include_test_data: bool = True,
                 include_output: bool = True,
                 ):
        self.include_test_data = include_test_data
        self.include_output = include_output

    def __eq__(self, other):
        if isinstance(other, MappingPackageV3LightweightLoader):
            return (self.include_test_data == other.include_test_data and
                    self.include_output == other.include_output)
        return False

    def load(self, package_folder_path: Path) -> MappingPackageV3Lightweight:
        """Load all components of a mapping package v3 lightweight (used in eForms).

        This method orchestrates the loading of:
        - Package metadata
        - Technical mapping suite
        - Vocabulary mapping suite

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            MappingPackageABC: Complete mapping package with all loaded components.
        """

        metadata = MappingPackageV3LightweightMetadataLoader().load(package_folder_path=package_folder_path,
                                                         relative_asset_path=mssdk_config.MPV3_METADATA_FILE_ASSET_PATH)


        technical_mapping_suite = TechnicalMappingSuiteLoader().load(package_folder_path=package_folder_path,
                                                                     relative_asset_path=mssdk_config.MPV3_TECHNICAL_COLLECTION_ASSET_PATH)

        vocabulary_mapping_suite = VocabularyMappingSuiteLoader().load(package_folder_path=package_folder_path,
                                                                       relative_asset_path=mssdk_config.MPV3_VOCABULARY_COLLECTION_ASSET_PATH)

        return MappingPackageV3Lightweight(
            metadata=metadata,
            technical_mapping_suite=technical_mapping_suite,
            vocabulary_mapping_suite=vocabulary_mapping_suite
        )
