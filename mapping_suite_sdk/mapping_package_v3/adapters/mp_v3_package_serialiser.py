from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser, \
    ConceptualMappingFileAssetSerialiser, TechnicalMappingCollectionAssetSerialiser, \
    VocabularyMappingCollectionAssetSerialiser, TestDataCollectionAssetSerialiser, SPARQLTestCollectionAssetSerialiser, \
    SHACLTestCollectionAssetSerialiser, TestResultCollectionAssetSerialiser
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_metadata_serialiser import MappingPackageV3MetadataSerialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


@traced_class
class MappingPackageV3Serialiser(MappingPackageAssetSerialiser):
    """Main serialiser for complete mapping packages."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV3) -> None:
        """Serialize all components of a mapping package.

        This method orchestrates the serialization of:
        - Package metadata
        - Conceptual mapping file
        - Technical mapping suite
        - Vocabulary mapping suite
        - Test data suites
        - SPARQL test suites
        - SHACL test suites

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            asset (MappingPackageABC): Complete mapping package to serialize.
        """

        # Serialize each component
        MappingPackageV3MetadataSerialiser().serialise(package_folder_path, asset.metadata)
        ConceptualMappingFileAssetSerialiser().serialise(package_folder_path, asset.conceptual_mapping_asset)
        TechnicalMappingCollectionAssetSerialiser().serialise(package_folder_path, asset.technical_mapping_suite)
        VocabularyMappingCollectionAssetSerialiser().serialise(package_folder_path, asset.vocabulary_mapping_suite)
        TestDataCollectionAssetSerialiser().serialise(package_folder_path, asset.test_data_suites)
        SPARQLTestCollectionAssetSerialiser().serialise(package_folder_path, asset.test_suites_sparql)
        SHACLTestCollectionAssetSerialiser().serialise(package_folder_path, asset.test_suites_shacl)
        TestResultCollectionAssetSerialiser().serialise(package_folder_path, asset.test_results)
