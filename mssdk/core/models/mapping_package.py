from typing import List

from pydantic import BaseModel, Field

from mssdk.core.models.core import CoreModel, STR_MIN_LENGTH, STR_MAX_LENGTH
from mssdk.core.models.files import ConceptualMappingFile, TechnicalMappingSuite, ValueMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite, TestResultSuite


class MappingPackageMetadata(CoreModel):
    """A class representing the metadata of a mapping package.

    This class contains essential identifying information and metadata about
    a mapping package, including its unique identifier, title, creation date,
    and type classification.
    """
    identifier: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH)
    title: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH)
    issue_date: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="created_at")
    type: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="mapping_type")


class MappingSource(CoreModel):
    """A class representing the source data configuration in a mapping package.

    This class defines the characteristics of the source data that will be
    transformed. It includes information about the source data format and version.
    """
    title: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH,
                       description="Example: Standard Forms XSD R09.S01")
    version: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="mapping_version")


class MappingTarget(CoreModel):
    """A class representing the target data configuration in a mapping package.

    This class defines the characteristics of the target data format that the
    source data will be transformed into. It includes information about the
    target ontology or data model and its version.
    """
    title: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, description="Example: ePO v4.0.0")
    version: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="ontology_version")


class MappingPackageEligibilityConstraints(CoreModel):
    """
        This shall be a generic dict-like structure as the constraints
        in the eForms are different from the constraints in the Standard Forms.
    """
    value: dict = Field(default_factory=dict, alias="metadata_constraints")


class MappingPackage(BaseModel):
    """
    A class representing a complete mapping package configuration.

    This class serves as the root container for all components of a mapping package,
    including metadata, mapping configurations, and various test suites. It provides
    a comprehensive structure for organizing and managing all aspects of a data
    mapping project.
    """

    # Metadata
    metadata: MappingPackageMetadata = Field(..., description="Package metadata containing general information")
    source: MappingSource = Field(..., description="Source data configuration and specifications")
    target: MappingTarget = Field(..., description="Target data configuration and specifications")
    eligibility_constraints: MappingPackageEligibilityConstraints = Field(...,
                                                                          description="Constraints defining package applicability")
    signature: bytes = Field(..., alias="mapping_suite_hash_digest", description="Package integrity hash")
    index: dict = Field(..., description="Index of package contents and their relationships")
    mapping_values: List[str] = Field(..., description="List of mapping value identifiers")

    # Package elements (folders and files)
    conceptual_mapping_file: ConceptualMappingFile = Field(..., description="The CMs in Excel Spreadsheet")
    technical_mapping_suite: TechnicalMappingSuite = Field(..., description="All teh RML files, which are RMLFragments")
    value_mapping_suite: ValueMappingSuite = Field(..., description="The resources JSONs, CSV and XML files")
    test_data_suites: List[TestDataSuite] = Field(..., description="Collections of test data for transformation")
    test_suites_sparql: List[SAPRQLTestSuite] = Field(..., description="Collections of SPARQL-based test suites")
    test_suites_shacl: List[SHACLTestSuite] = Field(...,
                                                    description="Collections of SHACL-based validation test suites")
    test_results: List[TestResultSuite] = Field(..., description="Collections of test transformation results")
