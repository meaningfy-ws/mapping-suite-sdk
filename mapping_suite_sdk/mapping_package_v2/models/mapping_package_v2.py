from typing import List

from pydantic import Field

from mapping_suite_sdk.core.models.collection_asset import TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset, TestDataCollectionAsset, SAPRQLTestCollectionAsset, SHACLTestCollectionAsset, \
    TestResultCollectionAsset
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata


# class MappingSource(PydanticModel):
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
# class MappingTarget(PydanticModel):
#     """A class representing the target data configuration in a mapping package.
#
#     This class defines the characteristics of the target data format that the
#     source data will be transformed into. It includes information about the
#     target ontology or data model and its version.
#     """
#     title: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, description="Example: ePO v4.0.0")
#     version: str = Field(..., min_length=STR_MIN_LENGTH, max_length=STR_MAX_LENGTH, alias="ontology_version")


class MappingPackageV2(MappingPackage):
    """
        A class representing a complete V2 (eForms) mapping package configuration.

        This class serves as the root container for all components of a mapping package,
        including metadata, mapping configurations, and various test suites. It provides
        a comprehensive structure for organizing and managing all aspects of a data
        mapping project.
    """

    # Metadata
    metadata: MappingPackageV2Metadata = Field(..., description="Package metadata containing general information")

    # Package elements (folders and files)
    conceptual_mapping_asset: ConceptualMappingFileAsset = Field(..., description="The CMs in Excel Spreadsheet")
    technical_mapping_suite: TechnicalMappingCollectionAsset = Field(...,
                                                                     description="All teh RML files, which are RMLFragments")
    vocabulary_mapping_suite: VocabularyMappingCollectionAsset = Field(...,
                                                                       description="The resources JSONs, CSV and XML files")
    test_data_suites: List[TestDataCollectionAsset] = Field(...,
                                                            description="Collections of test data for transformation")
    test_suites_sparql: List[SAPRQLTestCollectionAsset] = Field(...,
                                                                description="Collections of SPARQL-based test suites")
    test_suites_shacl: SHACLTestCollectionAsset = Field(...,
                                                        description="Collections of SHACL-based validation test suites")
    test_results: TestResultCollectionAsset = Field(..., description="Collections of test transformation results")

    @property
    def id(self) -> str:
        """Return the package identifier from metadata."""
        return self.metadata.identifier
