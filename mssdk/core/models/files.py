from abc import ABC
from enum import Enum
from pathlib import Path
from typing import List

from pydantic import Field

from mssdk.core.models.core import CoreModel


class MSSDKEnum(Enum):
    @classmethod
    def to_list(cls):
        return [member.value for member in cls]


class RMLFileSuffix(str, MSSDKEnum):
    TTL = ".ttl"
    RDF = ".rdf"
    N3 = ".n3"


class YARRRMLFileSuffix(str, MSSDKEnum):
    YARRRML = ".yarrrml"
    YML = ".yml"
    YAML = ".yaml"


### Files

class BaseFile(CoreModel):
    """A base class representing a file within a mapping package.

    This class serves as the foundation for all file types in the mapping suite,
    providing essential attributes and functionality for file handling. It manages
    both the location and content of a file, ensuring consistent file handling
    across different file types in the mapping package.
    """
    path: Path = Field(..., description="Path within a mapping package")
    content: str = Field(..., description="Content of the file")

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


class ConceptualMappingFile(BaseFile):
    """A class representing a Conceptual Mapping file.

    This class handles files that define high-level mapping concepts and relationships
    between source data and target ontologies or data models. Conceptual mappings
    typically describe the logical connections between different data elements without
    implementation details.
    """
    content: bytes = Field(..., description="xlsx file content in bytes")


class VocabularyMappingFile(BaseFile):
    """A class representing a Vocabulary Mapping file.

    This class manages files that define specific value transformations and mappings
    between source and target data values. Value mappings are used to specify how
    individual data values should be transformed, converted, or mapped to different
    formats or vocabularies.
    """
    pass


class SPARQLQueryFile(BaseFile):
    """A class representing a SPARQL Query file.

    This class handles files containing SPARQL ASK queries used for validating
    RDF data. ASK queries return a boolean result (true/false) indicating whether
    a given pattern exists in the data used for validation checks.
    """
    pass


class TestDataFile(BaseFile):
    """A class representing a Test Data file.

    This class manages files containing test data used for validating and verifying
    mapping transformations. Test data files typically include sample input data
    and expected output data to ensure mapping processes work correctly.
    """
    pass


class TestDataResultFile(BaseFile):
    """A class representing a test data result file.

    This class handles files that contain the actual output results from
    executing mapping transformations on test data. These files store the
    results of test data processing, allowing comparison between expected
    and actual outputs for validation and verification purposes. The results
    can be used to verify the correctness of mapping transformations and
    identify potential issues in the mapping process.
    """
    pass


class TechnicalMappingFile(BaseFile, ABC):
    """An abstract base class for Technical Mapping files.

    This class serves as a base for specific technical mapping implementations.
    Technical mappings contain the detailed, implementation-specific rules for
    transforming data from one format to another. This abstract class defines
    the common interface that all technical mapping implementations must follow.
    """
    pass


class RMLMappingFile(TechnicalMappingFile):
    """A class representing an RML (RDF Mapping Language) Mapping file.

    This class handles files containing RML mappings, which are used to express
    customized mappings from heterogeneous data structures and serializations to
    the RDF data model. RML is an extension of R2RML that enables mapping from
    various  tree-shaped data formats (CSV, XML, JSON) to RDF.
    """
    pass


class YARRRMLMappingFile(TechnicalMappingFile):
    """A class representing a YARRRML Mapping file.

    This class manages files containing YARRRML mappings, which are human-readable
    representations of RML mappings written in YAML syntax. YARRRML provides a more
    accessible way to write RML mappings while maintaining the same expressive power.
    """
    pass


### Suites

class BaseFileCollection(CoreModel):
    """A base class for managing collections of related files within a mapping package.

    This class serves as a foundation for organizing and managing groups of related files
    in a mapping package. It provides functionality to track both the location and content
    of file collections, making it easier to manage sets of related mapping artifacts.
    """
    path: Path = Field(..., description="Path within a mapping package")
    files: List[BaseFile] = Field(default_factory=list, description="Collection of files")


class TechnicalMappingSuite(BaseFileCollection):
    """A collection of technical mapping files.

    This suite manages a set of technical mapping files that together define the
    implementation-specific mapping rules. It can include various types of mapping
    files such as RML or YARRRML mappings that work together to achieve a complete
    data transformation solution.
    """
    pass


class VocabularyMappingSuite(BaseFileCollection):
    """A collection of value mapping files.

    This suite manages a set of value mapping files that define transformations
    for specific data values. It organizes files containing rules for value
    conversions, normalizations, and transformations that are applied during
    the mapping process.
    """
    pass


class TestDataSuite(BaseFileCollection):
    """A collection of test data files.

    This suite manages a set of test data files used for validation and verification
    of mapping processes. It typically includes input test data and their corresponding
    expected outputs used to verify the correctness of mapping transformations.
    """
    pass


class SAPRQLTestSuite(BaseFileCollection):
    """A collection of SPARQL test files.

    This suite manages a set of SPARQL query files used for testing and validation.
    It contains SPARQL queries that can be executed against mapped data to verify
    the correctness of the transformation results or to perform specific data
    validations.
    """
    pass


class SHACLTestSuite(BaseFileCollection):
    """A collection of SHACL test files.

    This suite manages a set of SHACL (Shapes Constraint Language) files used for
    RDF data validation. It contains SHACL shapes that define constraints and rules
    for validating the structure and content of RDF data produced by the mapping
    process.
    """
    pass


class TestResultSuite(BaseFileCollection):
    """A collection of test result files.

    This suite manages files containing the results of executed tests across
    the mapping suite. It stores the outputs and outcomes from various testing
    processes, which may include results from SPARQL queries, SHACL validations,
    and other test executions. These results can be used for validation,
    debugging, and quality assurance of the mapping processes.
    """
    pass
