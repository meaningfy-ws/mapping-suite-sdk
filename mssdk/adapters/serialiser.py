from pathlib import Path
from typing import Any, List, Protocol

from mssdk.adapters.loader import RELATIVE_TECHNICAL_MAPPING_SUITE_PATH, RELATIVE_VOCABULARY_MAPPING_SUITE_PATH, \
    RELATIVE_SUITE_METADATA_PATH, RELATIVE_CONCEPTUAL_MAPPING_PATH
from mssdk.models.files import (
    TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite,
    SAPRQLTestSuite, SHACLTestSuite, ConceptualMappingFile
)
from mssdk.models.mapping_package import MappingPackage, MappingPackageMetadata


class MappingPackageAssetSerializer(Protocol):
    """Protocol defining the interface for mapping package asset serializers.

    This protocol ensures that all asset serializers implement a consistent interface
    for serializing different components of a mapping package.
    """

    def serialize(self, package_folder_path: Path, asset: Any) -> None:
        """Serialize an asset to the specified package folder path.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            asset (Any): The asset to serialize.

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class.
        """
        raise NotImplementedError


class TechnicalMappingSuiteSerializer(MappingPackageAssetSerializer):
    """Serializer for technical mapping suite files."""

    def serialize(self, package_folder_path: Path, asset: TechnicalMappingSuite) -> None:
        suite_path = package_folder_path / RELATIVE_TECHNICAL_MAPPING_SUITE_PATH
        suite_path.mkdir(parents=True, exist_ok=True)

        for tm_file in asset.files:
            file_path = package_folder_path / tm_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(tm_file.content)


class VocabularyMappingSuiteSerializer(MappingPackageAssetSerializer):
    """Serializer for vocabulary mapping suite files."""

    def serialize(self, package_folder_path: Path, asset: VocabularyMappingSuite) -> None:
        suite_path = package_folder_path / RELATIVE_VOCABULARY_MAPPING_SUITE_PATH
        suite_path.mkdir(parents=True, exist_ok=True)

        for vm_file in asset.files:
            file_path = package_folder_path / vm_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(vm_file.content)


class TestDataSuitesSerializer(MappingPackageAssetSerializer):
    """Serializer for test data suites."""

    def serialize(self, package_folder_path: Path, asset: List[TestDataSuite]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for test_file in suite.files:
                file_path = package_folder_path / test_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(test_file.content)


class SPARQLTestSuitesSerializer(MappingPackageAssetSerializer):
    """Serializer for SPARQL test suites."""

    def serialize(self, package_folder_path: Path, asset: List[SAPRQLTestSuite]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for query_file in suite.files:
                file_path = package_folder_path / query_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(query_file.content)


class SHACLTestSuitesSerializer(MappingPackageAssetSerializer):
    """Serializer for SHACL test suites."""

    def serialize(self, package_folder_path: Path, asset: List[SHACLTestSuite]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for shape_file in suite.files:
                file_path = package_folder_path / shape_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(shape_file.content)


class MappingPackageMetadataSerializer(MappingPackageAssetSerializer):
    """Serializer for mapping package metadata."""

    def serialize(self, package_folder_path: Path, asset: MappingPackageMetadata) -> None:
        metadata_path = package_folder_path / RELATIVE_SUITE_METADATA_PATH
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(asset.model_dump_json(by_alias=True))


class ConceptualMappingFileSerializer(MappingPackageAssetSerializer):
    """Serializer for conceptual mapping files."""

    def serialize(self, package_folder_path: Path, asset: ConceptualMappingFile) -> None:
        file_path = package_folder_path / RELATIVE_CONCEPTUAL_MAPPING_PATH
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(asset.content)


class MappingPackageSerializer(MappingPackageAssetSerializer):
    """Main serializer for complete mapping packages."""

    def serialize(self, package_folder_path: Path, asset: MappingPackage) -> None:
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
            asset (MappingPackage): Complete mapping package to serialize.
        """

        # Serialize each component
        MappingPackageMetadataSerializer().serialize(package_folder_path, asset.metadata)
        ConceptualMappingFileSerializer().serialize(package_folder_path, asset.conceptual_mapping_file)
        TechnicalMappingSuiteSerializer().serialize(package_folder_path, asset.technical_mapping_suite)
        VocabularyMappingSuiteSerializer().serialize(package_folder_path, asset.vocabulary_mapping_suite)
        TestDataSuitesSerializer().serialize(package_folder_path, asset.test_data_suites)
        SPARQLTestSuitesSerializer().serialize(package_folder_path, asset.test_suites_sparql)
        SHACLTestSuitesSerializer().serialize(package_folder_path, asset.test_suites_shacl)
