from typing import List, Optional

from pydantic import Field
from mapping_suite_sdk.core.models.collection_asset import SHACLTestCollectionAsset, SPARQLTestCollectionAsset, TechnicalMappingCollectionAsset, TestDataCollectionAsset, TestResultCollectionAsset, VocabularyMappingCollectionAsset
from mapping_suite_sdk.core.models.file_asset import ConceptualMappingFileAsset
from mapping_suite_sdk.core.models.pydantic import PydanticModel


class MappingPackage(PydanticModel):
    """
        A base class representing the bare minimum of a mapping package across all versions/specializations of the model.
    """

    # Mandatory package elements without which transformation cannot occur
    technical_mapping_suite: TechnicalMappingCollectionAsset = Field(..., description="RML mapping files containing the technical mapping rules/definitions")
    vocabulary_mapping_suite: VocabularyMappingCollectionAsset = Field(..., description="Vocabulary resources used by mapping rules in XML, JSON or CSV format")

class MappingPackageCommon(MappingPackage):
    """
        A base class representing the common characteristics of a mapping package across some versions/specializations of the model.
    """

    # Common package elements
    conceptual_mapping_asset: Optional[ConceptualMappingFileAsset] = Field(None, description="The Conceptual Mapping (CM) in Excel (XLSX) spreadsheet format")
    test_data_suites: List[TestDataCollectionAsset] = Field(default_factory=list, description="List of test data collections in XML format")
    test_suites_sparql: List[SPARQLTestCollectionAsset] = Field(default_factory=list, description="List of SPARQL-based validation test suites")
    test_suites_shacl: Optional[SHACLTestCollectionAsset] = Field(None, description="Container for SHACL-based validation test suites")
    test_results: Optional[TestResultCollectionAsset] = Field(None, description="Container for transformation test results and outputs")
