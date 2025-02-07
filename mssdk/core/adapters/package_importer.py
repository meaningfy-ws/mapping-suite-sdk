import io
import tarfile
import xml.etree.ElementTree as ET
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd
import rarfile

from mssdk.core.models.mapping_package import MappingPackage, TestData, XMLTestFile, TransformationData, \
    ConceptualMapping, TechnicalMapping, ValidationData, SHACLShape, SPARQLQuery


class MappingPackageImportError(Exception):
    """Base exception for mapping package import errors"""
    pass


class UnsupportedArchiveFormat(MappingPackageImportError):
    """Raised when archive format is not supported"""
    pass


class InvalidPackageStructure(MappingPackageImportError):
    """Raised when package structure is invalid"""
    pass


class FileParsingError(MappingPackageImportError):
    """Raised when file parsing fails"""
    pass


# Abstract handler
class ArchiveHandler(ABC):
    """Base handler for the chain of responsibility"""

    def __init__(self):
        self._next_handler: Optional[ArchiveHandler] = None

    def set_next(self, handler: 'ArchiveHandler') -> 'ArchiveHandler':
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, file_path: str) -> dict:
        """Handle the archive format and return a dictionary of file contents"""
        if self._next_handler:
            return self._next_handler.handle(file_path)
        raise UnsupportedArchiveFormat(f"No handler found for file: {file_path}")


# Concrete handlers
class ZipHandler(ArchiveHandler):
    """Handler for ZIP archives"""

    def handle(self, file_path: str) -> dict:
        if not file_path.lower().endswith('.zip'):
            return super().handle(file_path)

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                return self._extract_files(zip_file)
        except zipfile.BadZipFile as e:
            raise MappingPackageImportError(f"Invalid ZIP file: {str(e)}")

    def _extract_files(self, zip_file: zipfile.ZipFile) -> dict:
        files = {}
        for file_info in zip_file.filelist:
            if not file_info.filename.endswith('/'):  # Skip directories
                with zip_file.open(file_info) as file:
                    files[file_info.filename] = file.read()
        return files


class RarHandler(ArchiveHandler):
    """Handler for RAR archives"""

    def handle(self, file_path: str) -> dict:
        if not file_path.lower().endswith('.rar'):
            return super().handle(file_path)

        try:
            with rarfile.RarFile(file_path, 'r') as rar_file:
                return self._extract_files(rar_file)
        except rarfile.BadRarFile as e:
            raise MappingPackageImportError(f"Invalid RAR file: {str(e)}")

    def _extract_files(self, rar_file: rarfile.RarFile) -> dict:
        files = {}
        for file_info in rar_file.infolist():
            if not file_info.isdir():  # Skip directories
                with rar_file.open(file_info) as file:
                    files[file_info.filename] = file.read()
        return files


class TarHandler(ArchiveHandler):
    """Handler for TAR archives"""

    def handle(self, file_path: str) -> dict:
        if not any(file_path.lower().endswith(ext) for ext in ['.tar', '.gz', '.tgz']):
            return super().handle(file_path)

        try:
            with tarfile.open(file_path, 'r:*') as tar_file:
                return self._extract_files(tar_file)
        except tarfile.TarError as e:
            raise MappingPackageImportError(f"Invalid TAR file: {str(e)}")

    def _extract_files(self, tar_file: tarfile.TarFile) -> dict:
        files = {}
        for member in tar_file.getmembers():
            if member.isfile():  # Skip directories
                file = tar_file.extractfile(member)
                if file:
                    files[member.name] = file.read()
        return files



class FileParser:
    """Helper class for parsing different file types"""

    @staticmethod
    def parse_xml(content: bytes) -> str:
        try:
            # Validate XML by parsing it
            ET.fromstring(content)
            return content.decode('utf-8')
        except ET.ParseError as e:
            raise FileParsingError(f"Invalid XML content: {str(e)}")

    @staticmethod
    def parse_excel(content: bytes) -> Dict[str, List[Dict[str, str]]]:
        try:
            df_dict = pd.read_excel(io.BytesIO(content), sheet_name=None)
            return {
                sheet_name: df.to_dict('records')
                for sheet_name, df in df_dict.items()
            }
        except Exception as e:
            raise FileParsingError(f"Failed to parse Excel file: {str(e)}")

    @staticmethod
    def parse_ttl(content: bytes) -> str:
        # Add TTL validation if needed
        return content.decode('utf-8')

    @staticmethod
    def parse_sparql(content: bytes) -> str:
        # Add SPARQL validation if needed
        return content.decode('utf-8')


# Main importer adapter
class MappingPackageImporter:
    """Adapter for importing mapping packages from archives"""

    def __init__(self):
        # Set up the chain of responsibility
        self.handler = ZipHandler()
        self.handler.set_next(RarHandler()).set_next(TarHandler())
        self.parser = FileParser()

    def import_package(self, file_path: str) -> MappingPackage:
        """Import a mapping package from an archive file"""
        # Extract files from archive
        files = self.handler.handle(file_path)

        # Validate package structure
        self._validate_structure(files)

        # Parse files and create MappingPackage
        return self._create_package(files)

    def _validate_structure(self, files: dict) -> None:
        """Validate the package structure"""
        required_folders = {'test/', 'transformation/', 'validation/'}
        file_paths = set(Path(f).parent.as_posix() + '/' for f in files.keys())

        if not all(any(path.startswith(folder) for path in file_paths)
                   for folder in required_folders):
            raise InvalidPackageStructure("Missing required folders")

    def _create_package(self, files: dict) -> MappingPackage:
        """Create a MappingPackage from extracted files"""
        test_data = self._process_test_data(files)
        transformation_data = self._process_transformation_data(files)
        validation_data = self._process_validation_data(files)

        return MappingPackage(
            package_name=Path(files[0]).stem,
            package_version="1.0.0",  # You might want to extract this from a metadata file
            test_data=test_data,
            transformation_data=transformation_data,
            validation_data=validation_data
        )

    def _process_test_data(self, files: dict) -> TestData:
        """Process test data files"""
        xml_files = []
        for filename, content in files.items():
            if filename.startswith('test/') and filename.lower().endswith('.xml'):
                xml_content = self.parser.parse_xml(content)
                xml_files.append(XMLTestFile(
                    name=Path(filename).name,
                    content=xml_content
                ))
        return TestData(files=xml_files)

    def _process_transformation_data(self, files: dict) -> TransformationData:
        """Process transformation data files"""
        conceptual_mapping = None
        technical_mappings = []

        for filename, content in files.items():
            if not filename.startswith('transformation/'):
                continue

            if filename.lower().endswith(('.xlsx', '.xls')):
                sheets_data = self.parser.parse_excel(content)
                conceptual_mapping = ConceptualMapping(
                    name=Path(filename).name,
                    sheets=sheets_data
                )
            elif filename.lower().endswith('.ttl'):
                ttl_content = self.parser.parse_ttl(content)
                technical_mappings.append(TechnicalMapping(
                    name=Path(filename).name,
                    content=ttl_content
                ))

        if not conceptual_mapping:
            raise InvalidPackageStructure("Missing conceptual mapping file")

        return TransformationData(
            conceptual_mapping=conceptual_mapping,
            technical_mappings=technical_mappings
        )

    def _process_validation_data(self, files: dict) -> ValidationData:
        """Process validation data files"""
        shacl_shapes = []
        sparql_queries = []

        for filename, content in files.items():
            if not filename.startswith('validation/'):
                continue

            if filename.lower().endswith('.ttl'):
                ttl_content = self.parser.parse_ttl(content)
                shacl_shapes.append(SHACLShape(
                    name=Path(filename).name,
                    content=ttl_content
                ))
            elif filename.lower().endswith(('.rq', '.sparql')):
                sparql_content = self.parser.parse_sparql(content)
                sparql_queries.append(SPARQLQuery(
                    name=Path(filename).name,
                    content=sparql_content
                ))

        return ValidationData(
            shacl_shapes=shacl_shapes,
            sparql_queries=sparql_queries
        )
