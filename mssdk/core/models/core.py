from abc import abstractmethod, ABC
from enum import Enum
from functools import cached_property

from lxml import etree
from pydantic import BaseModel, Field, field_validator, computed_field

STR_MIN_LENGTH = 1
STR_MAX_LENGTH = 256


class FileExtensionEnum(str, Enum):
    XML = 'xml'
    CSV = 'csv'
    XSLX = 'xslx'


class CoreModel(BaseModel):
    class Config:
        validate_assignment = True


class MappingSuiteFile(CoreModel, ABC):
    name: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH)
    content: str = Field(..., min_length=STR_MIN_LENGTH)

    @abstractmethod
    @computed_field
    @cached_property
    def extension(self) -> str:
        raise NotImplementedError

    @abstractmethod
    @field_validator("content")
    @classmethod
    def _validate_content(cls, file_content: str) -> str:
        raise NotImplementedError


class XMLTestDataFile(MappingSuiteFile):
    suite_name: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH)

    def extension(self) -> str:
        ext = self.name.split(".")[-1]
        if ext not in [FileExtensionEnum.XML]:
            raise ValueError(f"Invalid file extension: {ext}")

        return ext

    def _validate_content(cls, file_content: str) -> str:
        try:
            etree.fromstring(file_content)
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML: {e}")
        return file_content


class ConceptualMappingFile(MappingSuiteFile):
    pass


class TechnicalMappingFile(MappingSuiteFile):
    pass


class TMResourceFile(MappingSuiteFile):
    pass


class SHACLShapeFile(MappingSuiteFile):
    pass


class SPARQLQueryFile(MappingSuiteFile):
    pass


class MetadataFile(MappingSuiteFile):
    pass


class MappingPackage(CoreModel):
    metadata_file: MetadataFile

