from pathlib import Path
from typing import Protocol, Any, List, Union, Optional, NoReturn

from mapping_suite_sdk.core.models.collection_asset import TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset, TestDataCollectionAsset, SPARQLTestCollectionAsset, SHACLTestCollectionAsset, \
    TestResultCollectionAsset
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset


def write_file_by_content_type(file_path: Path, content: Union[str, bytes]) -> Optional[NoReturn]:
    """
    Write content to a file based on its content type (str or bytes).
    Raises exceptions if any errors occur during the process.

    Args:
        file_path: Path to the file
        content: Content to write, either string or bytes

    Returns:
        None if successful

    Raises:
        TypeError: If content is neither string nor bytes
        OSError: If file operations fail (permission issues, disk full, etc.)
        Exception: For any other unexpected errors
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        file_path.write_text(content)
    elif isinstance(content, bytes):
        file_path.write_bytes(content)
    else:
        raise TypeError(f"Content must be str or bytes, got {type(content).__name__}")

    return None


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


class TechnicalMappingCollectionAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for technical mapping suite files."""

    def serialise(self, package_folder_path: Path, asset: TechnicalMappingCollectionAsset) -> None:
        suite_path = package_folder_path / asset.path
        suite_path.mkdir(parents=True, exist_ok=True)

        for tm_file in asset.files:
            file_path = package_folder_path / tm_file.path
            write_file_by_content_type(file_path=file_path, content=tm_file.content)


class VocabularyMappingCollectionAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for vocabulary mapping suite files."""

    def serialise(self, package_folder_path: Path, asset: VocabularyMappingCollectionAsset) -> None:
        suite_path = package_folder_path / asset.path
        suite_path.mkdir(parents=True, exist_ok=True)

        for vm_file in asset.files:
            file_path = package_folder_path / vm_file.path
            write_file_by_content_type(file_path=file_path, content=vm_file.content)


class TestDataCollectionAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for test data suites."""

    def serialise(self, package_folder_path: Path, asset: List[TestDataCollectionAsset]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for test_file in suite.files:
                file_path = package_folder_path / test_file.path
                write_file_by_content_type(file_path=file_path, content=test_file.content)


class SPARQLTestCollectionAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for SPARQL test suites."""

    def serialise(self, package_folder_path: Path, asset: List[SPARQLTestCollectionAsset]) -> None:
        for suite in asset:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for query_file in suite.files:
                file_path = package_folder_path / query_file.path
                write_file_by_content_type(file_path=file_path, content=query_file.content)


class SHACLTestCollectionAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for SHACL test suites."""

    def serialise(self, package_folder_path: Path, asset: SHACLTestCollectionAsset) -> None:
        for suite in asset.shacl_collections:
            suite_path = package_folder_path / suite.path
            suite_path.mkdir(parents=True, exist_ok=True)

            for shape_file in suite.files:
                file_path = package_folder_path / shape_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(shape_file.content)

        shacl_result_query_path = package_folder_path / asset.shacl_result_query.path
        shacl_result_query_path.parent.mkdir(parents=True, exist_ok=True)
        shacl_result_query_path.write_text(asset.shacl_result_query.content)


class ConceptualMappingFileAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for conceptual mapping files."""

    def serialise(self, package_folder_path: Path, asset: ConceptualMappingFileAsset) -> None:
        file_path = package_folder_path / asset.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(asset.content)


class TestResultCollectionAssetSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for test result suites."""

    def serialise(self, package_folder_path: Path, asset: TestResultCollectionAsset) -> None:
        folder_path = package_folder_path
        for report in asset.files:
            report_path = folder_path / report.path
            write_file_by_content_type(file_path=report_path, content=report.content)

        for test_data_suite in asset.result_suites:

            # Could be, if output and test data are together
            # TestDataCollectionAssetSerialiser().serialise(folder_path, [test_data_suite])

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
