from pathlib import Path
from typing import Any, List, Protocol, Tuple

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.models.collection_asset import TestDataCollectionAsset, SPARQLTestCollectionAsset, \
    SHACLTestCollectionAsset, \
    TestResultCollectionAsset, TestDataResultCollectionAsset, TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset, SHACLShapesCollectionAsset
from mapping_suite_sdk.core.models.file_asset import RMLMappingFileAsset, VocabularyMappingFileAsset, TestDataFileAsset, \
    SPARQLQueryFileAsset, SHACLShapesFileAsset, ReportFileAsset, TestDataResultFileAsset, ConceptualMappingFileAsset, \
    SHACLShapesResultQueryFileAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage


def load_file_by_extensions(file_path: Path,
                            str_extensions: Tuple = mssdk_config.MSSDK_SUPPORTED_TEXT_FILE_EXTENSIONS,
                            bytes_extensions: Tuple = mssdk_config.MSSDK_SUPPORTED_BYTES_FILE_EXTENSIONS) -> str | bytes | None:
    """
    Load content from a file based on its extension.

    Args:
        file_path: Path to the file
        str_extensions: List of extensions to read as string (text mode)
        bytes_extensions: List of extensions to read as bytes (binary mode)

    Returns:
        File content as string or bytes depending on the extension,
        or None if the extension is not in either list
    """
    if not file_path.exists():
        return None

    if not file_path.is_file():
        return None

    extension = file_path.suffix.lower()

    if extension in str_extensions:
        return file_path.read_text()
    elif extension in bytes_extensions:
        with open(file_path, 'rb') as file:
            return file.read()
    else:
        return None


class Loader(Protocol):
    """Protocol defining the interface for loaders (of mapping packages, mapping suites, etc).

    This protocol ensures that all loaders implement a consistent interface
    for loading different components of a Thing.
    """

    def load(self, package_folder_path: Path) -> Any:
        """Load the mapping package from the specified package folder path.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            Any: The loaded package or mapping suite.

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class.
        """
        raise NotImplementedError


class AssetLoader(Protocol):
    """Protocol defining the interface for loaders of assets in mapping packages, or mapping suites

    This protocol ensures that all asset loaders implement a consistent interface
    for loading different components of a whole.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> Any:
        """Load an asset from the specified package folder path.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            Any: The loaded asset.

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class.
        """
        raise NotImplementedError


class TechnicalMappingSuiteLoader(AssetLoader):
    """Loader for technical mapping suite files.

    Handles loading of RML and YARRRML mapping files from the technical mapping suite directory.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> TechnicalMappingCollectionAsset:
        """Load technical mapping files from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            TechnicalMappingSuiteAsset: Collection of loaded RML and YARRRML mapping files.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path
        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
            package_folder_path = root_folder

        tm_files: List[RMLMappingFileAsset] = []

        for tm_file in asset_path.iterdir():
            if tm_file.is_file():
                tm_files.append(
                    RMLMappingFileAsset(path=tm_file.relative_to(package_folder_path), content=tm_file.read_text()))

        return TechnicalMappingCollectionAsset(path=asset_path.relative_to(package_folder_path), files=tm_files)


class VocabularyMappingSuiteLoader(AssetLoader):
    """Loader for vocabulary mapping suite files.

    Loads vocabulary mapping files that define term mappings and transformations.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> VocabularyMappingCollectionAsset:
        """Load vocabulary mapping files from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            VocabularyMappingSuiteAsset: Collection of loaded vocabulary mapping files.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path
        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
            package_folder_path = root_folder

        files: List[VocabularyMappingFileAsset] = []

        for file in asset_path.iterdir():
            if file.is_file():
                files.append(
                    VocabularyMappingFileAsset(path=file.relative_to(package_folder_path), content=file.read_text()))

        return VocabularyMappingCollectionAsset(path=asset_path.relative_to(package_folder_path), files=files)


class TestDataSuitesLoader(AssetLoader):
    """Loader for test data suites.

    Handles loading of test data files organized in test suites.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> List[TestDataCollectionAsset]:
        """Load test data suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            List[TestDataCollectionAsset]: List of test data suites, each containing test files.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path
        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
            package_folder_path = root_folder

        test_data_suites: List[TestDataCollectionAsset] = []
        for ts_suite in asset_path.iterdir():
            if ts_suite.is_dir():
                test_data_suites.append(TestDataCollectionAsset(path=ts_suite.relative_to(package_folder_path),
                                                                files=[
                                                                    TestDataFileAsset(
                                                                        path=ts_file.relative_to(package_folder_path),
                                                                        content=ts_file.read_text()) for ts_file in
                                                                    ts_suite.iterdir() if ts_file.is_file()]))
        return test_data_suites


class SPARQLTestSuitesLoader(AssetLoader):
    """Loader for SPARQL test suites.

    Handles loading of SPARQL query files organized in validation suites.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> List[SPARQLTestCollectionAsset]:
        """Load SPARQL validation suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            List[SPARQLTestCollectionAsset]: List of SPARQL validation suites.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path
        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
            package_folder_path = root_folder

        sparql_validation_suites: List[SPARQLTestCollectionAsset] = []
        for sparql_suite in asset_path.iterdir():
            if sparql_suite.is_dir():
                sparql_validation_suites.append(
                    SPARQLTestCollectionAsset(path=sparql_suite.relative_to(package_folder_path),
                                              files=[SPARQLQueryFileAsset(
                                                  path=ts_file.relative_to(package_folder_path),
                                                  content=ts_file.read_text()) for ts_file
                                                  in
                                                  sparql_suite.iterdir() if ts_file.is_file()]))
        return sparql_validation_suites


class SHACLTestSuitesLoader(AssetLoader):
    """Loader for SHACL test suites.

    Handles loading of SHACL shape files organized in validation suites.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> SHACLTestCollectionAsset:
        """Load SHACL validation suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            List[SHACLTestCollectionAsset]: List of SHACL validation suites.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path
        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
        else:
            root_folder = package_folder_path

        shacl_validation_suites: List[SHACLShapesCollectionAsset] = []
        for shacl_suite in asset_path.iterdir():
            if shacl_suite.is_dir():
                shacl_validation_suites.append(
                    SHACLShapesCollectionAsset(path=shacl_suite.relative_to(package_folder_path),
                                               files=[SHACLShapesFileAsset(
                                                   path=ts_file.relative_to(package_folder_path),
                                                   content=ts_file.read_text()) for ts_file
                                                   in
                                                   shacl_suite.iterdir() if ts_file.is_file()]))

        return SHACLTestCollectionAsset(
            path=relative_asset_path,
            shacl_result_query=SHACLShapesResultQueryFileAsset(
                path=mssdk_config.MPV1_SHACL_SHAPES_QUERY_FILE_ASSET_PATH,
                content=(root_folder / mssdk_config.MPV1_SHACL_SHAPES_QUERY_FILE_ASSET_PATH).read_text()
            ),
            shacl_collections=shacl_validation_suites
        )


class TestResultSuiteLoader(AssetLoader):
    """Loader for test result suite.

    Handles loading of test execution results.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> TestResultCollectionAsset:
        test_result_collection_asset = TestResultCollectionAsset(path=relative_asset_path)
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / test_result_collection_asset.path
        if root_folder.exists():
            asset_path = root_folder / test_result_collection_asset.path
            package_folder_path = root_folder

        test_result_collection_asset.files = [ReportFileAsset(
            path=report_path.relative_to(package_folder_path),
            content=load_file_by_extensions(report_path)
        ) for report_path in asset_path.iterdir() if report_path.is_file()]

        test_result_collection_asset.result_suites = [TestResultCollectionAsset(
            path=suite_path.relative_to(package_folder_path),
            files=[ReportFileAsset(
                path=report_path.relative_to(package_folder_path),
                content=load_file_by_extensions(report_path)
            ) for report_path in suite_path.iterdir() if report_path.is_file()],
            result_suites=[
                TestDataResultCollectionAsset(
                    path=test_data_suites_result.relative_to(package_folder_path),
                    files=[
                        ReportFileAsset(
                            path=test_data_report.relative_to(package_folder_path),
                            content=load_file_by_extensions(test_data_report)
                        )
                        for test_data_report in report_dir.iterdir()
                        if test_data_report.is_file()
                    ]
                    if report_dir.exists() and report_dir.is_dir()
                    else [],
                    test_data_output=TestDataResultFileAsset(
                        path=ttl_file.relative_to(package_folder_path),
                        content=load_file_by_extensions(ttl_file)),
                )
                for test_data_suites_result in suite_path.iterdir()
                if test_data_suites_result.is_dir()
                and (ttl_file := next(test_data_suites_result.glob('*.ttl'), None)) is not None
                and (report_dir := test_data_suites_result / "test_suite_report")
            ]
        ) for suite_path in asset_path.iterdir() if suite_path.is_dir()]

        return test_result_collection_asset


class ConceptualMappingFileLoader(AssetLoader):
    """Loader for conceptual mapping files.

    Handles loading of conceptual mapping Excel files.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> ConceptualMappingFileAsset:
        """Load the conceptual mapping Excel file.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            ConceptualMappingFileAsset: The loaded conceptual mapping file.
        """
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path
        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
            package_folder_path = root_folder

        return ConceptualMappingFileAsset(
            path=asset_path.relative_to(package_folder_path),
            content=asset_path.read_bytes()
        )

