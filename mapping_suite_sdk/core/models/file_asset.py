from abc import ABC
from pathlib import Path

from pydantic import Field

from mapping_suite_sdk.core.models.pydantic import PydanticModel


class FileAsset(PydanticModel):
    """A base class representing a file within a mapping package.

    This class serves as the foundation for all file types in the mapping suite,
    providing essential attributes and functionality for file handling. It manages
    both the location and content of a file, ensuring consistent file handling
    across different file types in the mapping package.
    """
    path: Path = Field(..., description="Path within a mapping package")
    content: str | bytes = Field(..., description="Content of the file")

    # Note: Potential future
    # @abstractmethod
    # @computed_field
    # @cached_property
    # def extension(self) -> str:
    #     raise NotImplementedError
    #
    # @abstractmethod
    # @field_validator("content")
    # @classmethod
    # def _validate_content(cls, file_content: str) -> str:
    #     raise NotImplementedError


class ConceptualMappingFileAsset(FileAsset):
    """A class representing a Conceptual Mapping file.

    This class handles files that define high-level mapping concepts and relationships
    between source data and target ontologies or data models. Conceptual mappings
    typically describe the logical connections between different data elements without
    implementation details.
    """
    path: Path = Field(..., description="Path within a mapping package")

    content: bytes = Field(..., description="xlsx file content in bytes")


class VocabularyMappingFileAsset(FileAsset):
    """A class representing a Vocabulary Mapping file.

    This class manages files that define specific value transformations and mappings
    between source and target data values. Value mappings are used to specify how
    individual data values should be transformed, converted, or mapped to different
    formats or vocabularies.
    """
    content: str = Field(..., description="Content of the file")


class SPARQLQueryFileAsset(FileAsset):
    """A class representing a SPARQL Query file.

    This class handles files containing SPARQL ASK queries used for validating
    RDF data. ASK queries return a boolean result (true/false) indicating whether
    a given pattern exists in the data used for validation checks.
    """
    content: str = Field(..., description="Content of the file")


class SHACLShapesFileAsset(FileAsset):
    """A class representing a SHACL (Shapes Constraint Language) Shapes file.

    This class handles files containing SHACL shapes which define constraints
    and rules for validating RDF data. Each shape describes the conditions that
    a set of RDF nodes must satisfy, including property values, cardinality,
    data types, and structural patterns. SHACL shapes can be used to validate
    instance data against predefined constraints and ensure data quality.
    """
    content: str = Field(..., description="Content of the file")


class SHACLShapesResultQueryFileAsset(SPARQLQueryFileAsset):
    """

    """
    content: str = Field(..., description="Content of the file")
    path: Path = Field(..., description="Path within a mapping package")


class TestDataFileAsset(FileAsset):
    __test__ = False
    """A class representing a Test Data file.

    This class manages files containing test data used for validating and verifying
    mapping transformations. Test data files typically include sample input data
    and expected output data to ensure mapping processes work correctly.
    """
    content: str = Field(..., description="Content of the file")


class TestDataResultFileAsset(FileAsset):
    __test__ = False
    """A class representing a test data result file.

    This class handles files that contain the actual output results from
    executing mapping transformations on test data. These files store the
    results of test data processing, allowing comparison between expected
    and actual outputs for validation and verification purposes. The results
    can be used to verify the correctness of mapping transformations and
    identify potential issues in the mapping process.
    """
    content: str = Field(..., description="Content of the file")


class TechnicalMappingFileAsset(FileAsset, ABC):
    """An abstract base class for Technical Mapping files.

    This class serves as a base for specific technical mapping implementations.
    Technical mappings contain the detailed, implementation-specific rules for
    transforming data from one format to another. This abstract class defines
    the common interface that all technical mapping implementations must follow.
    """
    content: str = Field(..., description="Content of the file")


class RMLMappingFileAsset(TechnicalMappingFileAsset):
    """A class representing an RML (RDF Mapping Language) Mapping file.

    This class handles files containing RML mappings, which are used to express
    customized mappings from heterogeneous data structures and serializations to
    the RDF data model. RML is an extension of R2RML that enables mapping from
    various  tree-shaped data formats (CSV, XML, JSON) to RDF.
    """
    content: str = Field(..., description="Content of the file")


class YARRRMLMappingFileAsset(TechnicalMappingFileAsset):
    """A class representing a YARRRML Mapping file.

    This class manages files containing YARRRML mappings, which are human-readable
    representations of RML mappings written in YAML syntax. YARRRML provides a more
    accessible way to write RML mappings while maintaining the same expressive power.
    """
    content: str = Field(..., description="Content of the file")


class ReportFileAsset(FileAsset):
    """

    """
    content: str | bytes = Field(..., description="Content of the file")
