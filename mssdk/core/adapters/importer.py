from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List

from mssdk.core.models.files import ConceptualMappingFile, TechnicalMappingSuite, ValueMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite
from mssdk.core.models.mapping_package import MappingPackage, MappingPackageMetadata, MappingPackageIndex


class PackageImportHandlerABC(ABC):

    @abstractmethod
    def extract(self, data: Any) -> Any:
        pass


class ConceptualMappingFileImporter(PackageImportHandlerABC):

    def extract(self, cm_path: Path) -> ConceptualMappingFile:
        ...


class TechnicalMappingSuiteImporter(PackageImportHandlerABC):

    def extract(self, tm_suite_path: Path) -> TechnicalMappingSuite:
        ...


class ValueMappingSuiteImporter(PackageImportHandlerABC):

    def extract(self, vm_suite_path: Path) -> ValueMappingSuite:
        ...


class TestDataSuitesImporter(PackageImportHandlerABC):

    def extract(self, td_suites_path: Path) -> List[TestDataSuite]:
        ...


class SAPRQLTestSuitesImporter(PackageImportHandlerABC):

    def extract(self, sparql_suites_path: Path) -> List[SAPRQLTestSuite]:
        ...


class SHACLTestSuitesImporter(PackageImportHandlerABC):

    def extract(self, shacl_suites_path: Path) -> List[SHACLTestSuite]:
        ...


class TestResultSuiteImporter(PackageImportHandlerABC):

    def extract(self, tr_suite_path: Path) -> TestResultSuite:
        ...


class MappingPackageMetadataImporter(PackageImportHandlerABC):

    def extract(self, mp_metadata_path: Path) -> MappingPackageMetadata:
        ...


class MappingPackageIndexImporter(PackageImportHandlerABC):

    def extract(self, index_path: Path) -> MappingPackageIndex:
        ...


class PackageImporter(PackageImportHandlerABC):

    def extract(self, package_path: Path) -> MappingPackage:
        ...
