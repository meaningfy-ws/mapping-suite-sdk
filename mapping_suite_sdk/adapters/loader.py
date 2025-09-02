import json
from pathlib import Path
from typing import Any, List, Protocol

from pydantic import TypeAdapter, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from mapping_suite_sdk.adapters.tracer import traced_class
from mapping_suite_sdk.models.asset import TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite, RMLMappingAsset, \
    ConceptualMappingPackageAsset, VocabularyMappingAsset, TestDataAsset, SPARQLQueryAsset, SHACLShapesAsset, \
    ReportAsset, TestDataResultCollection, TestDataResultAsset
from mapping_suite_sdk.models.mapping_package import MappingPackage, MappingPackageMetadata, MappingPackageIndex
from mapping_suite_sdk.utils import load_file_by_extensions

### Paths relative to mapping package
RELATIVE_TECHNICAL_MAPPING_SUITE_PATH = Path("transformation/mappings")
RELATIVE_VOCABULARY_MAPPING_SUITE_PATH = Path("transformation/resources")
RELATIVE_TEST_DATA_PATH = Path("test_data")
RELATIVE_SPARQL_SUITE_PATH = Path("validation/sparql")
RELATIVE_SHACL_SUITE_PATH = Path("validation/shacl")
RELATIVE_SUITE_METADATA_PATH = Path("metadata.json")
RELATIVE_CONCEPTUAL_MAPPING_PATH = Path("transformation/conceptual_mappings.xlsx")
RELATIVE_TEST_RESULT_PATH = Path("output")
RELATIVE_TEST_DATA_REPORTS_OUTPUT_PATH = Path("test_suite_report")


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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_TECHNICAL_MAPPING_SUITE_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_TECHNICAL_MAPPING_SUITE_PATH

        tm_files: List[RMLMappingAsset] = []

        for tm_file in asset_path.iterdir():
            if tm_file.is_file():
                tm_files.append(
                    RMLMappingAsset(path=tm_file.relative_to(package_folder_path), content=tm_file.read_text()))

        return TechnicalMappingSuite(path=asset_path.relative_to(package_folder_path), files=tm_files)


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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_VOCABULARY_MAPPING_SUITE_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_VOCABULARY_MAPPING_SUITE_PATH

        files: List[VocabularyMappingAsset] = []

        for file in asset_path.iterdir():
            if file.is_file():
                files.append(
                    VocabularyMappingAsset(path=file.relative_to(package_folder_path), content=file.read_text()))

        return VocabularyMappingSuite(path=asset_path.relative_to(package_folder_path), files=files)


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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_TEST_DATA_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_TEST_DATA_PATH

        test_data_suites: List[TestDataSuite] = []
        for ts_suite in asset_path.iterdir():
            if ts_suite.is_dir():
                test_data_suites.append(TestDataSuite(path=ts_suite.relative_to(package_folder_path),
                                                      files=[
                                                          TestDataAsset(path=ts_file.relative_to(package_folder_path),
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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_SPARQL_SUITE_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_SPARQL_SUITE_PATH

        sparql_validation_suites: List[SAPRQLTestSuite] = []
        for sparql_suite in asset_path.iterdir():
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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_SHACL_SUITE_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_SHACL_SUITE_PATH

        shacl_validation_suites: List[SHACLTestSuite] = []
        for shacl_suite in asset_path.iterdir():
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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_SUITE_METADATA_PATH

        if root_folder.exists():
            asset_path = root_folder / RELATIVE_SUITE_METADATA_PATH

        model_dict: dict = json.loads(asset_path.read_text())
        model_dict['path'] = asset_path.relative_to(package_folder_path)

        return TypeAdapter(MappingPackageMetadata).validate_python(model_dict)


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

    Handles loading of test execution results.
    """

    def load(self, package_folder_path: Path) -> TestResultSuite:
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_TEST_RESULT_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_TEST_RESULT_PATH

        test_result_path: Path = asset_path
        return TestResultSuite(
            path=test_result_path,
            files=[ReportAsset(
                path=report_path.relative_to(package_folder_path),
                content=load_file_by_extensions(report_path)
            ) for report_path in test_result_path.iterdir() if report_path.is_file()],
            result_suites=[TestResultSuite(
                path=suite_path.relative_to(package_folder_path),
                files=[ReportAsset(
                    path=report_path.relative_to(package_folder_path),
                    content=load_file_by_extensions(report_path)
                ) for report_path in suite_path.iterdir() if report_path.is_file()],
                result_suites=[TestDataResultCollection(
                    path=test_data_suites_result.relative_to(package_folder_path),
                    files=[ReportAsset(
                        path=test_data_report.relative_to(package_folder_path),
                        content=load_file_by_extensions(test_data_report)
                    ) for test_data_report in
                        (test_data_suites_result / RELATIVE_TEST_DATA_REPORTS_OUTPUT_PATH).iterdir() if
                        test_data_report.is_file()],
                    test_data_output=TestDataResultAsset(
                        path=next(test_data_suites_result.glob('*.ttl'), None).relative_to(package_folder_path),
                        content=load_file_by_extensions(next(test_data_suites_result.glob('*.ttl'), None))),
                ) for test_data_suites_result in suite_path.iterdir() if test_data_suites_result.is_dir()]
            ) for suite_path in test_result_path.iterdir() if suite_path.is_dir()]
        )


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
        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / RELATIVE_CONCEPTUAL_MAPPING_PATH
        if root_folder.exists():
            asset_path = root_folder / RELATIVE_CONCEPTUAL_MAPPING_PATH

        return ConceptualMappingPackageAsset(
            path=asset_path.relative_to(package_folder_path),
            content=asset_path.read_bytes()
        )


@traced_class
class MappingPackageLoader(MappingPackageAssetLoader):
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
        if isinstance(other, MappingPackageLoader):
            return (self.include_test_data == other.include_test_data and
                    self.include_output == other.include_output)
        return False

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
        validation_errors: List[InitErrorDetails] = []

        def _process_exception(exception):
            if type(exception) is FileNotFoundError:
                validation_errors.append(InitErrorDetails(
                    type="missing",
                    loc=(str(exception.filename),),
                    input=str(package_folder_path),
                    ctx={"error": str(exception)},
                ))
            elif type(exception) is json.decoder.JSONDecodeError:
                validation_errors.append(InitErrorDetails(
                    type=PydanticCustomError(
                        "metadata_JSON_decode_error",
                        "Ensure metadata.json is valid JSON."
                    ),
                    loc=('metadata.json',),
                    input=str(package_folder_path),
                    ctx={"error": str(exception)},
                ))
            else:
                raise exception

        try:
            metadata = MappingPackageMetadataLoader().load(package_folder_path)
        except Exception as e:
            _process_exception(e)
        try:
            conceptual_mapping_file = ConceptualMappingFileLoader().load(package_folder_path)
        except Exception as e:
            _process_exception(e)
        try:
            technical_mapping_suite = TechnicalMappingSuiteLoader().load(package_folder_path)
        except Exception as e:
            _process_exception(e)
        try:
            vocabulary_mapping_suite = VocabularyMappingSuiteLoader().load(package_folder_path)
        except Exception as e:
            _process_exception(e)
        try:
            if self.include_test_data:
                test_data_suites = TestDataSuitesLoader().load(package_folder_path)
            else:
                test_data_suites = []
        except Exception as e:
            _process_exception(e)
        try:
            test_suites_sparql = SPARQLTestSuitesLoader().load(package_folder_path)
        except Exception as e:
            _process_exception(e)
        try:
            test_suites_shacl = SHACLTestSuitesLoader().load(package_folder_path)
        except Exception as e:
            _process_exception(e)
        try:
            if self.include_output:
                test_results = TestResultSuiteLoader().load(package_folder_path)
            else:
                test_results = TestResultSuite(path=package_folder_path / RELATIVE_TEST_RESULT_PATH)
        except Exception as e:
            _process_exception(e)

        if len(validation_errors) > 0:
            raise ValidationError.from_exception_data(title="Mapping Package Validation Error",
                                                      line_errors=validation_errors)
        return MappingPackage(
            metadata=metadata,
            conceptual_mapping_asset=conceptual_mapping_file,
            technical_mapping_suite=technical_mapping_suite,
            vocabulary_mapping_suite=vocabulary_mapping_suite,
            test_data_suites=test_data_suites,
            test_suites_sparql=test_suites_sparql,
            test_suites_shacl=test_suites_shacl,
            test_results=test_results,
        )
