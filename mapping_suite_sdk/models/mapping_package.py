from typing import List, Optional

from pydantic import Field

from mapping_suite_sdk.models.core import CoreModel, MSSDK_STR_MIN_LENGTH, MSSDK_STR_MAX_LENGTH
from mapping_suite_sdk.models.asset import ConceptualMappingPackageAsset, TechnicalMappingSuite, VocabularyMappingSuite, TestDataSuite, \
    SAPRQLTestSuite, SHACLTestSuite


# class MappingSource(CoreModel):
#     """A class representing the source data configuration in a mapping package.
#
#     This class defines the characteristics of the source data that will be
#     transformed. It includes information about the source data format and version.
#     """
#     title: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH,
#                        description="Example: Standard Forms XSD R09.S01")
#     version: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="mapping_version")
#
#
# class MappingTarget(CoreModel):
#     """A class representing the target data configuration in a mapping package.
#
#     This class defines the characteristics of the target data format that the
#     source data will be transformed into. It includes information about the
#     target ontology or data model and its version.
#     """
#     title: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, description="Example: ePO v4.0.0")
#     version: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="ontology_version")


class MappingPackageEligibilityConstraints(CoreModel):
    """
        This shall be a generic dict-like structure as the constraints
        in the eForms are different from the constraints in the Standard Forms.
    """
    constraints: dict = Field(default_factory=dict)

    description: Optional[str] = Field(default=None, exclude=True)


class MappingPackageMetadata(CoreModel):
    """A class representing the metadata of a mapping package.

    This class contains essential identifying information and metadata about
    a mapping package, including its unique identifier, title, creation date,
    and type classification.
    """
    identifier: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH)
    title: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH)
    issue_date: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH, alias="created_at")
    type: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH, alias="mapping_type")

    # source: MappingSource = Field(..., description="Source data configuration and specifications")
    # target: MappingTarget = Field(..., description="Target data configuration and specifications")
    mapping_version: str = Field(..., description="Version of source data that will be mapped")
    ontology_version: str = Field(..., description="Version of target ontology")

    eligibility_constraints: MappingPackageEligibilityConstraints = Field(...,
                                                                          description="Constraints defining package applicability",
                                                                          alias="metadata_constraints")
    signature: str = Field(..., alias="mapping_suite_hash_digest", description="Package integrity hash")


class MappingPackageIndex(CoreModel):
    # TODO: Future implementation
    value: dict = Field(..., description="Index of package contents and their relationships")


class MappingPackage(CoreModel):
    """
    A class representing a complete mapping package configuration.

    This class serves as the root container for all components of a mapping package,
    including metadata, mapping configurations, and various test suites. It provides
    a comprehensive structure for organizing and managing all aspects of a data
    mapping project.
    """

    # Metadata
    metadata: MappingPackageMetadata = Field(..., description="Package metadata containing general information")

    # Note: To implement when index structure will be defined
    # index: MappingPackageIndex = Field(..., description="Index of package contents and their relationships")

    # Package elements (folders and files)
    conceptual_mapping_file: ConceptualMappingPackageAsset = Field(..., description="The CMs in Excel Spreadsheet")
    technical_mapping_suite: TechnicalMappingSuite = Field(..., description="All teh RML files, which are RMLFragments")
    vocabulary_mapping_suite: VocabularyMappingSuite = Field(..., description="The resources JSONs, CSV and XML files")
    test_data_suites: List[TestDataSuite] = Field(..., description="Collections of test data for transformation")
    test_suites_sparql: List[SAPRQLTestSuite] = Field(..., description="Collections of SPARQL-based test suites")
    test_suites_shacl: List[SHACLTestSuite] = Field(...,
                                                    description="Collections of SHACL-based validation test suites")
    # Note: To implement when import will require transform results
    # test_results: List[TestResultSuite] = Field(..., description="Collections of test transformation results")
