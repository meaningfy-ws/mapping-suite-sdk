import json
from pathlib import Path
from typing import Any, List, Protocol

from mssdk.core.models.files import TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite, BaseFile, RMLFileSuffix, RMLMappingFile, YARRRMLFileSuffix, \
    YARRRMLMappingFile, ConceptualMappingFile
from mssdk.core.models.mapping_package import MappingPackage, MappingPackageMetadata, MappingPackageIndex
from mssdk.core.services.tracing import trace_method

### Paths relative to mapping package
RELATIVE_TECHNICAL_MAPPING_SUITE_PATH = Path("transformation/mappings")
RELATIVE_VALUE_MAPPING_SUITE_PATH = Path("transformation/resources")
RELATIVE_TEST_DATA_PATH = Path("test_data")
RELATIVE_SPARQL_SUITE_PATH = Path("validation/sparql")
RELATIVE_SHACL_SUITE_PATH = Path("validation/shacl")
RELATIVE_SUITE_METADATA_PATH = Path("metadata.json")
RELATIVE_CONCEPTUAL_MAPPING_PATH = Path("transformation/conceptual_mappings.xlsx")


class PackageLoaderProtocol(Protocol):

    def load(self, package_path: Path) -> Any:
        raise NotImplementedError


class TechnicalMappingSuiteLoader(PackageLoaderProtocol):

    @trace_method("extract_technical_mapping")
    def load(self, package_path: Path) -> TechnicalMappingSuite:
        files: List[BaseFile] = []

        for file in (package_path / RELATIVE_TECHNICAL_MAPPING_SUITE_PATH).iterdir():
            if file.is_file():
                rml_suffixes: List[str] = RMLFileSuffix.to_list()
                yarrrml_suffixes: List[str] = YARRRMLFileSuffix.to_list()

                if file.suffix in rml_suffixes:
                    files.append(RMLMappingFile(path=file.relative_to(package_path), content=file.read_text()))
                if file.suffix in yarrrml_suffixes:
                    files.append(YARRRMLMappingFile(path=file.relative_to(package_path), content=file.read_text()))

        return TechnicalMappingSuite(path=RELATIVE_TECHNICAL_MAPPING_SUITE_PATH, files=files)


class VocabularyMappingSuiteLoader(PackageLoaderProtocol):

    @trace_method("extract_value_mapping_suite")
    def load(self, package_path: Path) -> VocabularyMappingSuite:
        files: List[BaseFile] = []

        for file in (package_path / RELATIVE_VALUE_MAPPING_SUITE_PATH).iterdir():
            if file.is_file():
                files.append(BaseFile(path=file.relative_to(package_path), content=file.read_text()))

        return VocabularyMappingSuite(path=RELATIVE_VALUE_MAPPING_SUITE_PATH, files=files)


class TestDataSuitesLoader(PackageLoaderProtocol):

    @trace_method("extract_test_data_suites")
    def load(self, package_path: Path) -> List[TestDataSuite]:
        test_data_suites: List[TestDataSuite] = []
        for ts_suite in (package_path / RELATIVE_TEST_DATA_PATH).iterdir():
            if ts_suite.is_dir():
                test_data_suites.append(TestDataSuite(path=ts_suite.relative_to(package_path),
                                                      files=[BaseFile(path=ts_file.relative_to(package_path),
                                                                      content=ts_file.read_text()) for ts_file in
                                                             ts_suite.iterdir() if ts_file.is_file()]))
        return test_data_suites


class SPARQLTestSuitesLoader(PackageLoaderProtocol):

    @trace_method("extract_sparql_test_suites")
    def load(self, package_path: Path) -> List[SAPRQLTestSuite]:
        sparql_validation_suites: List[SAPRQLTestSuite] = []
        for sparql_suite in (package_path / RELATIVE_SPARQL_SUITE_PATH).iterdir():
            if sparql_suite.is_dir():
                sparql_validation_suites.append(SAPRQLTestSuite(path=sparql_suite.relative_to(package_path),
                                                                files=[BaseFile(path=ts_file.relative_to(package_path),
                                                                                content=ts_file.read_text()) for ts_file
                                                                       in
                                                                       sparql_suite.iterdir() if ts_file.is_file()]))
        return sparql_validation_suites


class SHACLTestSuitesLoader(PackageLoaderProtocol):

    @trace_method("extract_shacl_test_suites")
    def load(self, package_path: Path) -> List[SHACLTestSuite]:
        shacl_validation_suites: List[SHACLTestSuite] = []
        for shacl_suite in (package_path / RELATIVE_SHACL_SUITE_PATH).iterdir():
            if shacl_suite.is_dir():
                shacl_validation_suites.append(SHACLTestSuite(path=shacl_suite.relative_to(package_path),
                                                              files=[BaseFile(path=ts_file.relative_to(package_path),
                                                                              content=ts_file.read_text()) for ts_file
                                                                     in
                                                                     shacl_suite.iterdir() if ts_file.is_file()]))
        return shacl_validation_suites


class MappingPackageMetadataLoader(PackageLoaderProtocol):

    @trace_method("extract_mapping_package_metadata")
    def load(self, package_path: Path) -> MappingPackageMetadata:
        metadata_file_path: Path = package_path / RELATIVE_SUITE_METADATA_PATH
        metadata_file_dict: dict = json.loads(metadata_file_path.read_text())
        return MappingPackageMetadata(**metadata_file_dict)


class MappingPackageIndexLoader(PackageLoaderProtocol):

    @trace_method("extract_mapping_package_index")
    def load(self, package_path: Path) -> MappingPackageIndex:
        raise NotImplementedError


class TestResultSuiteLoader(PackageLoaderProtocol):

    @trace_method("extract_transform_result_suite")
    def load(self, package_path: Path) -> TestResultSuite:
        raise NotImplementedError


class ConceptualMappingFileLoader(PackageLoaderProtocol):

    def load(self, package_path: Path) -> ConceptualMappingFile:
        cm_file_path: Path = package_path / RELATIVE_CONCEPTUAL_MAPPING_PATH

        return ConceptualMappingFile(
            path=RELATIVE_CONCEPTUAL_MAPPING_PATH,
            content=cm_file_path.read_bytes()
        )


class PackageLoader(PackageLoaderProtocol):

    @trace_method("extract_mapping_package")
    def load(self, package_path: Path) -> MappingPackage:
        metadata = MappingPackageMetadataLoader().load(package_path)
        conceptual_mapping_file = ConceptualMappingFileLoader().load(package_path)
        technical_mapping_suite = TechnicalMappingSuiteLoader().load(package_path)
        vocabulary_mapping_suite = VocabularyMappingSuiteLoader().load(package_path)
        test_data_suites = TestDataSuitesLoader().load(package_path)
        test_suites_sparql = SPARQLTestSuitesLoader().load(package_path)
        test_suites_shacl = SHACLTestSuitesLoader().load(package_path)

        return MappingPackage(
            metadata=metadata,
            conceptual_mapping_file=conceptual_mapping_file,
            technical_mapping_suite=technical_mapping_suite,
            vocabulary_mapping_suite=vocabulary_mapping_suite,
            test_data_suites=test_data_suites,
            test_suites_sparql=test_suites_sparql,
            test_suites_shacl=test_suites_shacl
        )
