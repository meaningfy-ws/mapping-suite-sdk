from pathlib import Path
from typing import Any, List, Protocol

from mssdk.core.models.files import ConceptualMappingFile, TechnicalMappingSuite, ValueMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite, BaseFile
from mssdk.core.models.mapping_package import MappingPackage, MappingPackageMetadata, MappingPackageIndex

### Paths relative to mapping package
RELATIVE_TECHNICAL_MAPPING_SUITE_PATH = Path("transformation/mappings")
RELATIVE_VALUE_MAPPING_SUITE_PATH = Path("transformation/resources")


class PackageImportProtocol(Protocol):

    def extract(self, package_path: Path) -> Any:
        pass


class ConceptualMappingFileImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> ConceptualMappingFile:
        ...


class TechnicalMappingSuiteImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> TechnicalMappingSuite:
        files: List[BaseFile] = []

        for file in (package_path / RELATIVE_TECHNICAL_MAPPING_SUITE_PATH).iterdir():
            if file.is_file():
                files.append(BaseFile(path=file.relative_to(package_path), content=file.read_text()))

        return TechnicalMappingSuite(path=RELATIVE_TECHNICAL_MAPPING_SUITE_PATH, files=files)


class ValueMappingSuiteImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> ValueMappingSuite:
        files: List[BaseFile] = []

        for file in (package_path / RELATIVE_VALUE_MAPPING_SUITE_PATH).iterdir():
            if file.is_file():
                files.append(BaseFile(path=file.relative_to(package_path), content=file.read_text()))

        return ValueMappingSuite(path=RELATIVE_VALUE_MAPPING_SUITE_PATH, files=files)


class TestDataSuitesImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> List[TestDataSuite]:
        ...


class SAPRQLTestSuitesImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> List[SAPRQLTestSuite]:
        ...


class SHACLTestSuitesImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> List[SHACLTestSuite]:
        ...


class TestResultSuiteImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> TestResultSuite:
        ...


class MappingPackageMetadataImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> MappingPackageMetadata:
        ...


class MappingPackageIndexImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> MappingPackageIndex:
        ...


class PackageImporter:

    def extract(self, package_path: Path) -> MappingPackage:
        ...
