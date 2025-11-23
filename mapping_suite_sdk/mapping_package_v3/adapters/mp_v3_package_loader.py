from pathlib import Path

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.loader import Loader, ConceptualMappingFileLoader, \
    TechnicalMappingSuiteLoader, VocabularyMappingSuiteLoader, TestDataSuitesLoader, SPARQLTestSuitesLoader, \
    SHACLTestSuitesLoader, TestResultSuiteLoader
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.models.collection_asset import TestResultCollectionAsset
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_metadata_loader import MappingPackageV3MetadataLoader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


@traced_class
class MappingPackageV3Loader(Loader):
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
        if isinstance(other, MappingPackageV3Loader):
            return (self.include_test_data == other.include_test_data and
                    self.include_output == other.include_output)
        return False

    def load(self, package_folder_path: Path) -> MappingPackageV3:
        """Load all components of a mapping package v2 (used in eForms).

        This method orchestrates the loading of:
        - Package metadata
        - Conceptual mapping file
        - Technical mapping suite
        - Vocabulary mapping suite
        - Test data suites
        - SPARQL test suites
        - SHACL test suites

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            MappingPackageABC: Complete mapping package with all loaded components.
        """

        metadata = MappingPackageV3MetadataLoader().load(package_folder_path=package_folder_path,
                                                         relative_asset_path=mssdk_config.MPV3_METADATA_FILE_ASSET_PATH)

        conceptual_mapping_file = ConceptualMappingFileLoader().load(package_folder_path=package_folder_path,
                                                                     relative_asset_path=mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH)

        technical_mapping_suite = TechnicalMappingSuiteLoader().load(package_folder_path=package_folder_path,
                                                                     relative_asset_path=mssdk_config.MPV3_TECHNICAL_COLLECTION_ASSET_PATH)

        vocabulary_mapping_suite = VocabularyMappingSuiteLoader().load(package_folder_path=package_folder_path,
                                                                       relative_asset_path=mssdk_config.MPV3_VOCABULARY_COLLECTION_ASSET_PATH)
        if self.include_test_data:
            test_data_suites = TestDataSuitesLoader().load(package_folder_path=package_folder_path,
                                                           relative_asset_path=mssdk_config.MPV3_TEST_DATA_COLLECTION_ASSET_PATH)
        else:
            test_data_suites = []

        test_suites_sparql = SPARQLTestSuitesLoader().load(package_folder_path=package_folder_path,
                                                           relative_asset_path=mssdk_config.MPV3_SPARQL_TEST_COLLECTION_ASSET_PATH, )

        test_suites_shacl = SHACLTestSuitesLoader().load(package_folder_path=package_folder_path,
                                                         relative_asset_path=mssdk_config.MPV3_SHACL_TEST_COLLECTION_ASSET_PATH, )

        if self.include_output:
            test_results = TestResultSuiteLoader().load(package_folder_path=package_folder_path,
                                                        relative_asset_path=mssdk_config.MPV3_TEST_RESULT_COLLECTION_ASSET_PATH, )
        else:
            test_results = TestResultCollectionAsset(
                path=mssdk_config.MPV3_TEST_RESULT_COLLECTION_ASSET_PATH,
            )

        return MappingPackageV3(
            metadata=metadata,
            conceptual_mapping_asset=conceptual_mapping_file,
            technical_mapping_suite=technical_mapping_suite,
            vocabulary_mapping_suite=vocabulary_mapping_suite,
            test_data_suites=test_data_suites,
            test_suites_sparql=test_suites_sparql,
            test_suites_shacl=test_suites_shacl,
            test_results=test_results,
        )
