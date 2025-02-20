from pathlib import Path
from typing import Any, List, Protocol

from pydantic import TypeAdapter

from mapping_suite_sdk.models.asset import TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite, RMLMappingAsset, \
    ConceptualMappingPackageAsset, VocabularyMappingAsset, TestDataAsset, SPARQLQueryAsset, SHACLShapesAsset
from mapping_suite_sdk.models.mapping_package import MappingPackage, MappingPackageMetadata, MappingPackageIndex

### Paths relative to mapping package
RELATIVE_TECHNICAL_MAPPING_SUITE_PATH = Path("transformation/mappings")
RELATIVE_VOCABULARY_MAPPING_SUITE_PATH = Path("transformation/resources")
RELATIVE_TEST_DATA_PATH = Path("test_data")
RELATIVE_SPARQL_SUITE_PATH = Path("validation/sparql")
RELATIVE_SHACL_SUITE_PATH = Path("validation/shacl")
RELATIVE_SUITE_METADATA_PATH = Path("metadata.json")
RELATIVE_CONCEPTUAL_MAPPING_PATH = Path("transformation/conceptual_mappings.xlsx")


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

    def load(self, package_folder_path: Path) -> TechnicalMappingSuite:
        """Load technical mapping files from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            TechnicalMappingSuite: Collection of loaded RML and YARRRML mapping files.
        """
        tm_files: List[RMLMappingAsset] = []

        for tm_file in (package_folder_path / RELATIVE_TECHNICAL_MAPPING_SUITE_PATH).iterdir():
            if tm_file.is_file():
                tm_files.append(
                    RMLMappingAsset(path=tm_file.relative_to(package_folder_path), content=tm_file.read_text()))

        return TechnicalMappingSuite(path=RELATIVE_TECHNICAL_MAPPING_SUITE_PATH, files=tm_files)


class VocabularyMappingSuiteLoader(MappingPackageAssetLoader):
    """Loader for vocabulary mapping suite files.

    Loads vocabulary mapping files that define term mappings and transformations.
    """

    def load(self, package_folder_path: Path) -> VocabularyMappingSuite:
        """Load vocabulary mapping files from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            VocabularyMappingSuite: Collection of loaded vocabulary mapping files.
        """
        files: List[VocabularyMappingAsset] = []

        for file in (package_folder_path / RELATIVE_VOCABULARY_MAPPING_SUITE_PATH).iterdir():
            if file.is_file():
                files.append(
                    VocabularyMappingAsset(path=file.relative_to(package_folder_path), content=file.read_text()))

        return VocabularyMappingSuite(path=RELATIVE_VOCABULARY_MAPPING_SUITE_PATH, files=files)


class TestDataSuitesLoader(MappingPackageAssetLoader):
    """Loader for test data suites.

    Handles loading of test data files organized in test suites.
    """

    def load(self, package_folder_path: Path) -> List[TestDataSuite]:
        """Load test data suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            List[TestDataSuite]: List of test data suites, each containing test files.
        """
        test_data_suites: List[TestDataSuite] = []
        for ts_suite in (package_folder_path / RELATIVE_TEST_DATA_PATH).iterdir():
            if ts_suite.is_dir():
                test_data_suites.append(TestDataSuite(path=ts_suite.relative_to(package_folder_path),
                                                      files=[TestDataAsset(path=ts_file.relative_to(package_folder_path),
                                                                           content=ts_file.read_text()) for ts_file in
                                                             ts_suite.iterdir() if ts_file.is_file()]))
        return test_data_suites


class SPARQLTestSuitesLoader(MappingPackageAssetLoader):
    """Loader for SPARQL test suites.

    Handles loading of SPARQL query files organized in validation suites.
    """

    def load(self, package_folder_path: Path) -> List[SAPRQLTestSuite]:
        """Load SPARQL validation suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            List[SAPRQLTestSuite]: List of SPARQL validation suites.
        """
        sparql_validation_suites: List[SAPRQLTestSuite] = []
        for sparql_suite in (package_folder_path / RELATIVE_SPARQL_SUITE_PATH).iterdir():
            if sparql_suite.is_dir():
                sparql_validation_suites.append(SAPRQLTestSuite(path=sparql_suite.relative_to(package_folder_path),
                                                                files=[SPARQLQueryAsset(
                                                                    path=ts_file.relative_to(package_folder_path),
                                                                    content=ts_file.read_text()) for ts_file
                                                                    in
                                                                    sparql_suite.iterdir() if ts_file.is_file()]))
        return sparql_validation_suites


class SHACLTestSuitesLoader(MappingPackageAssetLoader):
    """Loader for SHACL test suites.

    Handles loading of SHACL shape files organized in validation suites.
    """

    def load(self, package_folder_path: Path) -> List[SHACLTestSuite]:
        """Load SHACL validation suites from the package.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            List[SHACLTestSuite]: List of SHACL validation suites.
        """
        shacl_validation_suites: List[SHACLTestSuite] = []
        for shacl_suite in (package_folder_path / RELATIVE_SHACL_SUITE_PATH).iterdir():
            if shacl_suite.is_dir():
                shacl_validation_suites.append(SHACLTestSuite(path=shacl_suite.relative_to(package_folder_path),
                                                              files=[SHACLShapesAsset(
                                                                  path=ts_file.relative_to(package_folder_path),
                                                                  content=ts_file.read_text()) for ts_file
                                                                  in
                                                                  shacl_suite.iterdir() if ts_file.is_file()]))
        return shacl_validation_suites


class MappingPackageMetadataLoader(MappingPackageAssetLoader):
    """Loader for mapping package metadata.

    Handles loading and parsing of the package metadata JSON file.
    """

    def load(self, package_folder_path: Path) -> MappingPackageMetadata:
        """Load metadata from the package's metadata.json file.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            MappingPackageMetadata: Parsed metadata object.
        """
        metadata_file_path: Path = package_folder_path / RELATIVE_SUITE_METADATA_PATH
        return TypeAdapter(MappingPackageMetadata).validate_json(metadata_file_path.read_text())


class MappingPackageIndexLoader(MappingPackageAssetLoader):
    """Loader for mapping package index.

    [Not implemented] Handles loading of package index information.
    """

    def load(self, package_folder_path: Path) -> MappingPackageIndex:
        """Load the mapping package index.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            MappingPackageIndex: The loaded package index.

        Raises:
            NotImplementedError: This loader is not yet implemented.
        """
        raise NotImplementedError


class TestResultSuiteLoader(MappingPackageAssetLoader):
    """Loader for test result suite.

    [Not implemented] Handles loading of test execution results.
    """

    def load(self, package_folder_path: Path) -> TestResultSuite:
        """Load test result suite.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            TestResultSuite: The loaded test results.

        Raises:
            NotImplementedError: This loader is not yet implemented.
        """
        raise NotImplementedError


class ConceptualMappingFileLoader(MappingPackageAssetLoader):
    """Loader for conceptual mapping files.

    Handles loading of conceptual mapping Excel files.
    """

    def load(self, package_folder_path: Path) -> ConceptualMappingPackageAsset:
        """Load the conceptual mapping Excel file.

        Args:
            package_folder_path (Path): Path to the mapping package folder.

        Returns:
            ConceptualMappingPackageAsset: The loaded conceptual mapping file.
        """
        cm_file_path: Path = package_folder_path / RELATIVE_CONCEPTUAL_MAPPING_PATH

        return ConceptualMappingPackageAsset(
            path=RELATIVE_CONCEPTUAL_MAPPING_PATH,
            content=cm_file_path.read_bytes()
        )


class MappingPackageLoader(MappingPackageAssetLoader):
    """Main loader for complete mapping packages.

    Coordinates the loading of all components of a mapping package using specialized loaders.
    """

    def load(self, package_folder_path: Path) -> MappingPackage:
        """Load all components of a mapping package.

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
            MappingPackage: Complete mapping package with all loaded components.
        """
        metadata = MappingPackageMetadataLoader().load(package_folder_path)
        conceptual_mapping_file = ConceptualMappingFileLoader().load(package_folder_path)
        technical_mapping_suite = TechnicalMappingSuiteLoader().load(package_folder_path)
        vocabulary_mapping_suite = VocabularyMappingSuiteLoader().load(package_folder_path)
        test_data_suites = TestDataSuitesLoader().load(package_folder_path)
        test_suites_sparql = SPARQLTestSuitesLoader().load(package_folder_path)
        test_suites_shacl = SHACLTestSuitesLoader().load(package_folder_path)

        return MappingPackage(
            metadata=metadata,
            conceptual_mapping_file=conceptual_mapping_file,
            technical_mapping_suite=technical_mapping_suite,
            vocabulary_mapping_suite=vocabulary_mapping_suite,
            test_data_suites=test_data_suites,
            test_suites_sparql=test_suites_sparql,
            test_suites_shacl=test_suites_shacl
        )
