from pathlib import Path
from typing import Any, List, Protocol

from mapping_suite_sdk.core.models.collection_asset import TestDataCollectionAsset, SAPRQLTestCollectionAsset, \
    SHACLTestCollectionAsset, \
    TestResultCollectionAsset, TestDataResultCollectionAsset, TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset, SHACLShapesCollectionAsset
from mapping_suite_sdk.core.models.file_asset import RMLMappingFileAsset, VocabularyMappingFileAsset, TestDataFileAsset, \
    SPARQLQueryFileAsset, SHACLShapesFileAsset, ReportFileAsset, TestDataResultFileAsset, ConceptualMappingFileAsset, \
    SHACLShapesResultQueryFileAsset
from mapping_suite_sdk.utils import load_file_by_extensions


class MappingPackageAssetLoader(Protocol):
    """Protocol defining the interface for mapping package asset loaders.

    This protocol ensures that all asset loaders implement a consistent interface
    for loading different components of a mapping package.
    """

    def load(self, package_folder_path: Path) -> Any:
        """Load an asset from the specified package folder path.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            Any: The loaded asset.

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class.
        """
        raise NotImplementedError


class TechnicalMappingSuiteLoader(MappingPackageAssetLoader):
    """Loader for technical mapping suite files.

    Handles loading of RML and YARRRML mapping files from the technical mapping suite directory.
    """

    def load(self, package_folder_path: Path) -> TechnicalMappingCollectionAsset:
        """Load technical mapping files from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            TechnicalMappingSuiteAsset: Collection of loaded RML and YARRRML mapping files.
        """
        relative_technical_mapping_suite_path = Path("transformation/mappings")

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_technical_mapping_suite_path
        if root_folder.exists():
            asset_path = root_folder / relative_technical_mapping_suite_path

        tm_files: List[RMLMappingFileAsset] = []

        for tm_file in asset_path.iterdir():
            if tm_file.is_file():
                tm_files.append(
                    RMLMappingFileAsset(path=tm_file.relative_to(package_folder_path), content=tm_file.read_text()))

        return TechnicalMappingCollectionAsset(path=asset_path.relative_to(package_folder_path), files=tm_files)


class VocabularyMappingSuiteLoader(MappingPackageAssetLoader):
    """Loader for vocabulary mapping suite files.

    Loads vocabulary mapping files that define term mappings and transformations.
    """

    def load(self, package_folder_path: Path) -> VocabularyMappingCollectionAsset:
        """Load vocabulary mapping files from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            VocabularyMappingSuiteAsset: Collection of loaded vocabulary mapping files.
        """
        relative_vocabulary_mapping_suite_path = Path("transformation/resources")

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_vocabulary_mapping_suite_path
        if root_folder.exists():
            asset_path = root_folder / relative_vocabulary_mapping_suite_path

        files: List[VocabularyMappingFileAsset] = []

        for file in asset_path.iterdir():
            if file.is_file():
                files.append(
                    VocabularyMappingFileAsset(path=file.relative_to(package_folder_path), content=file.read_text()))

        return VocabularyMappingCollectionAsset(path=asset_path.relative_to(package_folder_path), files=files)


class TestDataSuitesLoader(MappingPackageAssetLoader):
    """Loader for test data suites.

    Handles loading of test data files organized in test suites.
    """

    def load(self, package_folder_path: Path) -> List[TestDataCollectionAsset]:
        """Load test data suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            List[TestDataCollectionAsset]: List of test data suites, each containing test files.
        """
        relative_test_data_path = Path("test_data")

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_test_data_path
        if root_folder.exists():
            asset_path = root_folder / relative_test_data_path

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


class SPARQLTestSuitesLoader(MappingPackageAssetLoader):
    """Loader for SPARQL test suites.

    Handles loading of SPARQL query files organized in validation suites.
    """

    def load(self, package_folder_path: Path) -> List[SAPRQLTestCollectionAsset]:
        """Load SPARQL validation suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            List[SAPRQLTestCollectionAsset]: List of SPARQL validation suites.
        """
        relative_sparql_suite_path = Path("validation/sparql")

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_sparql_suite_path
        if root_folder.exists():
            asset_path = root_folder / relative_sparql_suite_path

        sparql_validation_suites: List[SAPRQLTestCollectionAsset] = []
        for sparql_suite in asset_path.iterdir():
            if sparql_suite.is_dir():
                sparql_validation_suites.append(
                    SAPRQLTestCollectionAsset(path=sparql_suite.relative_to(package_folder_path),
                                              files=[SPARQLQueryFileAsset(
                                                  path=ts_file.relative_to(package_folder_path),
                                                  content=ts_file.read_text()) for ts_file
                                                  in
                                                  sparql_suite.iterdir() if ts_file.is_file()]))
        return sparql_validation_suites


class SHACLTestSuitesLoader(MappingPackageAssetLoader):
    """Loader for SHACL test suites.

    Handles loading of SHACL shape files organized in validation suites.
    """

    def load(self, package_folder_path: Path) -> SHACLTestCollectionAsset:
        """Load SHACL validation suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            List[SHACLTestCollectionAsset]: List of SHACL validation suites.
        """
        relative_sparql_suite_path = Path("validation/shacl")

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_sparql_suite_path
        if root_folder.exists():
            asset_path = root_folder / relative_sparql_suite_path

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
            shacl_result_query=SHACLShapesResultQueryFileAsset(
                content=(asset_path / "shacl_result_query.rq").read_text()),
            shacl_collections=shacl_validation_suites
        )


class TestResultSuiteLoader(MappingPackageAssetLoader):
    """Loader for test result suite.

    Handles loading of test execution results.
    """

    def load(self, package_folder_path: Path) -> TestResultCollectionAsset:
        test_result_collection_asset = TestResultCollectionAsset()
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / test_result_collection_asset.path
        if root_folder.exists():
            asset_path = root_folder / test_result_collection_asset.path

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
            result_suites=[TestDataResultCollectionAsset(
                path=test_data_suites_result.relative_to(package_folder_path),
                files=[ReportFileAsset(
                    path=test_data_report.relative_to(package_folder_path),
                    content=load_file_by_extensions(test_data_report)
                ) for test_data_report in
                    (test_data_suites_result / "test_suite_report").iterdir() if
                    test_data_report.is_file()],
                test_data_output=TestDataResultFileAsset(
                    path=next(test_data_suites_result.glob('*.ttl'), None).relative_to(package_folder_path),
                    content=load_file_by_extensions(next(test_data_suites_result.glob('*.ttl'), None))),
            ) for test_data_suites_result in suite_path.iterdir() if test_data_suites_result.is_dir()]
        ) for suite_path in asset_path.iterdir() if suite_path.is_dir()]

        return test_result_collection_asset


class ConceptualMappingFileLoader(MappingPackageAssetLoader):
    """Loader for conceptual mapping files.

    Handles loading of conceptual mapping Excel files.
    """

    def load(self, package_folder_path: Path) -> ConceptualMappingFileAsset:
        """Load the conceptual mapping Excel file.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            ConceptualMappingFileAsset: The loaded conceptual mapping file.
        """
        relative_cm_path = Path("transformation/conceptual_mappings.xlsx")
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_cm_path
        if root_folder.exists():
            asset_path = root_folder / relative_cm_path

        return ConceptualMappingFileAsset(
            path=asset_path.relative_to(package_folder_path),
            content=asset_path.read_bytes()
        )
