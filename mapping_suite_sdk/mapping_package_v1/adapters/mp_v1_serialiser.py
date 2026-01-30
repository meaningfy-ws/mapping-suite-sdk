from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser, \
    ConceptualMappingFileAssetSerialiser, TechnicalMappingCollectionAssetSerialiser, \
    VocabularyMappingCollectionAssetSerialiser, TestDataCollectionAssetSerialiser, SPARQLTestCollectionAssetSerialiser, \
    SHACLTestCollectionAssetSerialiser, TestResultCollectionAssetSerialiser
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.models.pydantic import fields
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1_metadata import MappingPackageV1Metadata


class MappingPackageV1MetadataSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for mapping package metadata."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV1Metadata) -> None:
        metadata_path = package_folder_path / asset.path
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(asset.model_dump_json(by_alias=True,
                                                       exclude={fields(MappingPackageV1Metadata).path},
                                                       exclude_none=True,
                                                       # For V1 (Standard Forms)
                                                       indent=2))


@traced_class
class MappingPackageV1Serialiser(MappingPackageAssetSerialiser):
    """Main serialiser for complete mapping packages."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV1) -> None:
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
        MappingPackageV1MetadataSerialiser().serialise(package_folder_path, asset.metadata)
        ConceptualMappingFileAssetSerialiser().serialise(package_folder_path, asset.conceptual_mapping_asset)
        TechnicalMappingCollectionAssetSerialiser().serialise(package_folder_path, asset.technical_mapping_suite)
        VocabularyMappingCollectionAssetSerialiser().serialise(package_folder_path, asset.vocabulary_mapping_suite)
        TestDataCollectionAssetSerialiser().serialise(package_folder_path, asset.test_data_suites)
        SPARQLTestCollectionAssetSerialiser().serialise(package_folder_path, asset.test_suites_sparql)
        SHACLTestCollectionAssetSerialiser().serialise(package_folder_path, asset.test_suites_shacl)
        TestResultCollectionAssetSerialiser().serialise(package_folder_path, asset.test_results)
