import io
import xml.etree.ElementTree as ET
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from mssdk.core.models.mapping_package import MappingPackage
from mssdk.core.services.tracing import trace_method, tracer


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


class ArchiveHandler(ABC):
    """Base handler for the chain of responsibility"""

    def __init__(self):
        self._next_handler: Optional[ArchiveHandler] = None

    def set_next(self, handler: 'ArchiveHandler') -> 'ArchiveHandler':
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, file_path: str) -> dict:
        if self._next_handler:
            return self._next_handler.handle(file_path)
        raise UnsupportedArchiveFormat(f"No handler found for file: {file_path}")


class ZipHandler(ArchiveHandler):
    @trace_method("handle_zip_archive")
    def handle(self, file_path: str) -> dict:
        current_span = trace.get_current_span()
        current_span.set_attribute("archive.type", "zip")
        current_span.set_attribute("archive.path", file_path)

        if not file_path.lower().endswith('.zip'):
            return super().handle(file_path)

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                return self._extract_files(zip_file)
        except zipfile.BadZipFile as e:
            current_span.set_status(Status(StatusCode.ERROR), str(e))
            raise MappingPackageImportError(f"Invalid ZIP file: {str(e)}")

    @trace_method("extract_zip_files")
    def _extract_files(self, zip_file: zipfile.ZipFile) -> dict:
        current_span = trace.get_current_span()
        files = {}
        for file_info in zip_file.filelist:
            if not file_info.filename.endswith('/'):
                with zip_file.open(file_info) as file:
                    files[file_info.filename] = file.read()
        current_span.set_attribute("files.count", len(files))
        return files


class FileParser:
    """Helper class for parsing different file types"""

    @staticmethod
    @trace_method("parse_xml")
    def parse_xml(content: bytes) -> str:
        current_span = trace.get_current_span()
        try:
            ET.fromstring(content)
            return content.decode('utf-8')
        except ET.ParseError as e:
            current_span.set_status(Status(StatusCode.ERROR), str(e))
            raise FileParsingError(f"Invalid XML content: {str(e)}")

    @staticmethod
    @trace_method("parse_excel")
    def parse_excel(content: bytes) -> Dict[str, List[Dict[str, str]]]:
        current_span = trace.get_current_span()
        try:
            df_dict = pd.read_excel(io.BytesIO(content), sheet_name=None)
            result = {
                sheet_name: df.to_dict('records')
                for sheet_name, df in df_dict.items()
            }
            current_span.set_attribute("excel.sheets", len(result))
            return result
        except Exception as e:
            current_span.set_status(Status(StatusCode.ERROR), str(e))
            raise FileParsingError(f"Failed to parse Excel file: {str(e)}")


class MappingPackageImporter:
    def __init__(self):
        self.handler = ZipHandler()
        self.parser = FileParser()

    @trace_method("import_package")
    def import_package(self, file_path: str) -> MappingPackage:
        current_span = trace.get_current_span()
        current_span.set_attribute("package.path", file_path)

        try:
            files = self.handler.handle(file_path)
            self._validate_structure(files)
            package = self._create_package(files)
            current_span.set_attribute("package.name", package.package_name)
            return package
        except Exception as e:
            current_span.set_status(Status(StatusCode.ERROR), str(e))
            raise

    @trace_method("validate_structure")
    def _validate_structure(self, files: dict) -> None:
        current_span = trace.get_current_span()
        required_folders = {'test/', 'transformation/', 'validation/'}
        file_paths = set(Path(f).parent.as_posix() + '/' for f in files.keys())

        current_span.set_attribute("files.count", len(files))

        if not all(any(path.startswith(folder) for path in file_paths)
                   for folder in required_folders):
            current_span.set_status(Status(StatusCode.ERROR), "Missing required folders")
            raise InvalidPackageStructure("Missing required folders")

    @trace_method("create_package")
    def _create_package(self, files: dict) -> MappingPackage:
        with tracer.start_span("process_components") as span:
            test_data = self._process_test_data(files)
            transformation_data = self._process_transformation_data(files)
            validation_data = self._process_validation_data(files)

            span.set_attribute("test_files.count", len(test_data.files))
            span.set_attribute("technical_mappings.count",
                               len(transformation_data.technical_mappings))

        return MappingPackage(
            package_name=Path(files[0]).stem,
            package_version="1.0.0",
            test_data=test_data,
            transformation_data=transformation_data,
            validation_data=validation_data
        )
