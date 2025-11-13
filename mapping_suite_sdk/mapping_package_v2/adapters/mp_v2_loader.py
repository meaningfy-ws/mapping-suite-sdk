import json
from pathlib import Path

from pydantic import TypeAdapter

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.loader import AssetLoader, ConceptualMappingFileLoader, \
    TechnicalMappingSuiteLoader, VocabularyMappingSuiteLoader, TestDataSuitesLoader, SPARQLTestSuitesLoader, \
    SHACLTestSuitesLoader, TestResultSuiteLoader, Loader
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.models.collection_asset import TestResultCollectionAsset
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata


class MappingPackageV2MetadataLoader(AssetLoader):
    """Loader for mapping package metadata.

    Handles loading and parsing of the package metadata JSON file.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> MappingPackageV2Metadata:
        """Load metadata from the package's metadata.json file.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            MappingPackageMetadata: Parsed metadata object.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path

        if root_folder.exists():
            asset_path = root_folder / relative_asset_path

        model_dict: dict = json.loads(asset_path.read_text())
        model_dict['path'] = asset_path.relative_to(package_folder_path)

        return TypeAdapter(MappingPackageV2Metadata).validate_python(model_dict)


@traced_class
class MappingPackageV2Loader(Loader):
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
        if isinstance(other, MappingPackageV2Loader):
            return (self.include_test_data == other.include_test_data and
                    self.include_output == other.include_output)
        return False

    def load(self, package_folder_path: Path) -> MappingPackageV2:
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

        metadata = MappingPackageV2MetadataLoader().load(package_folder_path=package_folder_path,
                                                         relative_asset_path=mssdk_config.MPV2_METADATA_FILE_ASSET_PATH)

        conceptual_mapping_file = ConceptualMappingFileLoader().load(package_folder_path=package_folder_path,
                                                                     relative_asset_path=mssdk_config.MPV2_CONCEPTUAL_MAPPING_FILE_ASSET_PATH)

        technical_mapping_suite = TechnicalMappingSuiteLoader().load(package_folder_path=package_folder_path,
                                                                     relative_asset_path=mssdk_config.MPV2_TECHNICAL_COLLECTION_ASSET_PATH)

        vocabulary_mapping_suite = VocabularyMappingSuiteLoader().load(package_folder_path=package_folder_path,
                                                                       relative_asset_path=mssdk_config.MPV2_VOCABULARY_COLLECTION_ASSET_PATH)
        if self.include_test_data:
            test_data_suites = TestDataSuitesLoader().load(package_folder_path=package_folder_path,
                                                           relative_asset_path=mssdk_config.MPV2_TEST_DATA_COLLECTION_ASSET_PATH)
        else:
            test_data_suites = []

        test_suites_sparql = SPARQLTestSuitesLoader().load(package_folder_path=package_folder_path,
                                                           relative_asset_path=mssdk_config.MPV2_SPARQL_TEST_COLLECTION_ASSET_PATH, )

        test_suites_shacl = SHACLTestSuitesLoader().load(package_folder_path=package_folder_path,
                                                         relative_asset_path=mssdk_config.MPV2_SHACL_TEST_COLLECTION_ASSET_PATH, )

        if self.include_output:
            test_results = TestResultSuiteLoader().load(package_folder_path=package_folder_path,
                                                        relative_asset_path=mssdk_config.MPV2_TEST_RESULT_COLLECTION_ASSET_PATH, )
        else:
            test_results = TestResultCollectionAsset(
                path=mssdk_config.MPV2_TEST_RESULT_COLLECTION_ASSET_PATH,
            )

        return MappingPackageV2(
            metadata=metadata,
            conceptual_mapping_asset=conceptual_mapping_file,
            technical_mapping_suite=technical_mapping_suite,
            vocabulary_mapping_suite=vocabulary_mapping_suite,
            test_data_suites=test_data_suites,
            test_suites_sparql=test_suites_sparql,
            test_suites_shacl=test_suites_shacl,
            test_results=test_results,
        )
