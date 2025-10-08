from typing import List

from pydantic import Field

from mapping_suite_sdk.core.models.collection_asset import TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset, TestDataCollectionAsset, SAPRQLTestCollectionAsset, SHACLTestCollectionAsset, \
    TestResultCollectionAsset
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata


class MappingPackageV3(MappingPackage):
    """
        A class representing a complete V3 (Unified) mapping package configuration.

        This class serves as the root container for all components of a mapping package,
        including metadata, mapping configurations, and various test suites. It provides
        a comprehensive structure for organizing and managing all aspects of a data
        mapping project.
    """

    # Metadata
    metadata: MappingPackageV3Metadata = Field(..., description="Package metadata containing general information")

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
