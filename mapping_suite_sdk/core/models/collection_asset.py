from pathlib import Path
from typing import List, Union

from pydantic import Field

from mapping_suite_sdk.core.models.file_asset import FileAsset, TechnicalMappingFileAsset, VocabularyMappingFileAsset, \
    TestDataFileAsset, SPARQLQueryFileAsset, SHACLShapesFileAsset, ReportFileAsset, TestDataResultFileAsset, \
    SHACLShapesResultQueryFileAsset
from mapping_suite_sdk.core.models.pydantic import PydanticModel


class CollectionAsset(PydanticModel):
    """A base class for managing collections of related files within a mapping package.

    This class serves as a foundation for organizing and managing groups of related files
    in a mapping package. It provides functionality to track both the location and content
    of file collections, making it easier to manage sets of related mapping artifacts.
    """
    path: Path = Field(..., description="Path within a mapping package")
    files: List[FileAsset] = Field(default_factory=list, description="Collection of files")


class VocabularyMappingCollectionAsset(CollectionAsset):
    """

    """
    path: Path = Field(..., description="Path within a mapping package")
    files: List[VocabularyMappingFileAsset] = Field(default_factory=list, description="Collection of vocabulary files")


class TechnicalMappingCollectionAsset(CollectionAsset):
    """

    """
    path: Path = Field(..., description="Path within a mapping package")
    files: List[TechnicalMappingFileAsset] = Field(default_factory=list,
                                                   description="Collection of technical mapping files")


class TestDataCollectionAsset(CollectionAsset):
    """A collection of test data files.

    This suite manages a set of test data files used for validation and verification
    of mapping processes. It typically includes input test data and their corresponding
    expected outputs used to verify the correctness of mapping transformations.
    """
    path: Path = Field(..., description="Path within a mapping package")
    files: List[TestDataFileAsset] = Field(default_factory=list, description="Collection of test data files")


class SAPRQLTestCollectionAsset(CollectionAsset):
    """A collection of SPARQL test files.

    This suite manages a set of SPARQL query files used for testing and validation.
    It contains SPARQL queries that can be executed against mapped data to verify
    the correctness of the transformation results or to perform specific data
    validations.
    """
    path: Path = Field(..., description="Path within a mapping package")
    files: List[SPARQLQueryFileAsset] = Field(default_factory=list, description="Collection of SPARQL validation files")


class SHACLShapesCollectionAsset(CollectionAsset):
    files: List[SHACLShapesFileAsset] = Field(default_factory=list, description="Collection of SHACL shape files")


class SHACLTestCollectionAsset(CollectionAsset):
    """A collection of SHACL test files.

    This suite manages a set of SHACL (Shapes Constraint Language) files used for
    RDF data validation. It contains SHACL shapes that define constraints and rules
    for validating the structure and content of RDF data produced by the mapping
    process.
    """
    shacl_collections: List[SHACLShapesCollectionAsset] = Field(default_factory=list,
                                                                description="Collection of SHACL shape files")
    path: Path = Field(..., description="Path within a mapping package")
    shacl_result_query: SHACLShapesResultQueryFileAsset = Field(default=None, description="SHACL result query")


class TestDataResultCollectionAsset(CollectionAsset):
    files: List[ReportFileAsset] = Field(default_factory=list, description="Collection of reports for a suite of tests")
    test_data_output: TestDataResultFileAsset


class TestResultCollectionAsset(CollectionAsset):
    files: List[ReportFileAsset] = Field(default_factory=list, description="Collection of reports for a suite of tests")
    result_suites: List[Union['TestResultCollectionAsset', TestDataResultCollectionAsset]] = Field(default_factory=list,
                                                                                                   description="Collection of test result suites")
    path: Path = Field(..., description="Path within a mapping package")
