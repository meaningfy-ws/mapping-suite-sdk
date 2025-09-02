from pathlib import Path
from typing import Any, List, Protocol

from mapping_suite_sdk.adapters.tracer import traced_class
from mapping_suite_sdk.models.asset import (
    TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite,
    SAPRQLTestSuite, SHACLTestSuite, ConceptualMappingPackageAsset, TestResultSuite
)
from mapping_suite_sdk.models.core import fields
from mapping_suite_sdk.models.mapping_package import MappingPackage, MappingPackageMetadata
from mapping_suite_sdk.utils import write_file_by_content_type


class MappingPackageAssetSerialiser(Protocol):
    """Protocol defining the interface for mapping package asset serialisers.

    This protocol ensures that all asset serialisers implement a consistent interface
    for serializing different components of a mapping package.
    """

    def serialise(self, package_folder_path: Path, asset: Any) -> None:
        """Serialize an asset to the specified package folder path.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            asset (Any): The asset to serialize.

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class.
        """
        raise NotImplementedError


class TechnicalMappingSuiteSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for technical mapping suite files."""

    def serialise(self, package_folder_path: Path, asset: TechnicalMappingSuite) -> None:
        suite_path = package_folder_path / asset.path
        suite_path.mkdir(parents=True, exist_ok=True)

        for tm_file in asset.files:
            file_path = package_folder_path / tm_file.path
            write_file_by_content_type(file_path=file_path, content=tm_file.content)


class VocabularyMappingSuiteSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for vocabulary mapping suite files."""

    def serialise(self, package_folder_path: Path, asset: VocabularyMappingSuite) -> None:
        suite_path = package_folder_path / asset.path
        suite_path.mkdir(parents=True, exist_ok=True)

        for vm_file in asset.files:
            file_path = package_folder_path / vm_file.path
            write_file_by_content_type(file_path=file_path, content=vm_file.content)


class TestDataSuitesSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for test data suites."""

    def serialise(self, package_folder_path: Path, asset: List[TestDataSuite]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for test_file in suite.files:
                file_path = package_folder_path / test_file.path
                write_file_by_content_type(file_path=file_path, content=test_file.content)


class SPARQLTestSuitesSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for SPARQL test suites."""

    def serialise(self, package_folder_path: Path, asset: List[SAPRQLTestSuite]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for query_file in suite.files:
                file_path = package_folder_path / query_file.path
                write_file_by_content_type(file_path=file_path, content=query_file.content)


class SHACLTestSuitesSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for SHACL test suites."""

    def serialise(self, package_folder_path: Path, asset: List[SHACLTestSuite]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for shape_file in suite.files:
                file_path = package_folder_path / shape_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(shape_file.content)


class MappingPackageMetadataSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for mapping package metadata."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageMetadata) -> None:
        metadata_path = package_folder_path / asset.path
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        # TODO: We need somehow to store metadata file content separately in case the ident is different
        metadata_path.write_text(asset.model_dump_json(by_alias=True,
                                                       exclude={fields(MappingPackageMetadata).path},
                                                       indent=4))


class ConceptualMappingFileSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for conceptual mapping files."""

    def serialise(self, package_folder_path: Path, asset: ConceptualMappingPackageAsset) -> None:
        file_path = package_folder_path / asset.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(asset.content)


class TestResultSuiteSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for test result suites."""

    def serialise(self, package_folder_path: Path, asset: TestResultSuite) -> None:
        folder_path = package_folder_path
        for report in asset.files:
            report_path = folder_path / report.path
            write_file_by_content_type(file_path=report_path, content=report.content)

        for test_data_suite in asset.result_suites:

            # Could be, if output and test data are together
            # TestDataSuitesSerialiser().serialise(folder_path, [test_data_suite])

            for test_suite_report in test_data_suite.files:
                test_suite_report_path = folder_path / test_suite_report.path
                write_file_by_content_type(file_path=test_suite_report_path, content=test_suite_report.content)

            for test_data_result_collection in test_data_suite.result_suites:
                test_data_result_path = folder_path / test_data_result_collection.test_data_output.path
                write_file_by_content_type(file_path=test_data_result_path,
                                           content=test_data_result_collection.test_data_output.content)

                for test_data_result_reports in test_data_result_collection.files:
                    test_data_result_reports_path = folder_path / test_data_result_reports.path
                    write_file_by_content_type(file_path=test_data_result_reports_path,
                                               content=test_data_result_reports.content)


@traced_class
class MappingPackageSerialiser(MappingPackageAssetSerialiser):
    """Main serialiser for complete mapping packages."""

    def serialise(self, package_folder_path: Path, asset: MappingPackage) -> None:
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
        MappingPackageMetadataSerialiser().serialise(package_folder_path, asset.metadata)
        ConceptualMappingFileSerialiser().serialise(package_folder_path, asset.conceptual_mapping_asset)
        TechnicalMappingSuiteSerialiser().serialise(package_folder_path, asset.technical_mapping_suite)
        VocabularyMappingSuiteSerialiser().serialise(package_folder_path, asset.vocabulary_mapping_suite)
        TestDataSuitesSerialiser().serialise(package_folder_path, asset.test_data_suites)
        SPARQLTestSuitesSerialiser().serialise(package_folder_path, asset.test_suites_sparql)
        SHACLTestSuitesSerialiser().serialise(package_folder_path, asset.test_suites_shacl)
        TestResultSuiteSerialiser().serialise(package_folder_path, asset.test_results)
