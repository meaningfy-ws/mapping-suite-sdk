from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List

from mssdk.core.models.files import ConceptualMappingFile, TechnicalMappingSuite, ValueMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite, BaseFile
from mssdk.core.models.mapping_package import MappingPackage, MappingPackageMetadata, MappingPackageIndex

### Paths relative to mapping package
RELATIVE_TECHNICAL_MAPPING_PATH = Path("transformation/mappings")


class PackageImportHandlerABC(ABC):

    @abstractmethod
    def extract(self, package_path: Path, data: Any) -> Any:
        pass


class ConceptualMappingFileImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, cm_path: Path) -> ConceptualMappingFile:
        ...


class TechnicalMappingSuiteImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, tm_suite_path: Path) -> TechnicalMappingSuite:
        files: List[BaseFile] = []

        for file in (package_path / tm_suite_path).iterdir():
            if file.is_file():
                files.append(BaseFile(path=file.relative_to(package_path), content=file.read_text()))

        return TechnicalMappingSuite(path=tm_suite_path, files=files)


class ValueMappingSuiteImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, vm_suite_path: Path) -> ValueMappingSuite:
        ...


class TestDataSuitesImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, td_suites_path: Path) -> List[TestDataSuite]:
        ...


class SAPRQLTestSuitesImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, sparql_suites_path: Path) -> List[SAPRQLTestSuite]:
        ...


class SHACLTestSuitesImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, shacl_suites_path: Path) -> List[SHACLTestSuite]:
        ...


class TestResultSuiteImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, tr_suite_path: Path) -> TestResultSuite:
        ...


class MappingPackageMetadataImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, mp_metadata_path: Path) -> MappingPackageMetadata:
        ...


class MappingPackageIndexImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path, index_path: Path) -> MappingPackageIndex:
        ...


class PackageImporter:

    def extract(self, package_path: Path) -> MappingPackage:
        ...
