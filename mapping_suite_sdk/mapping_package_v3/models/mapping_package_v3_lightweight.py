from typing import List

from pydantic import Field

from mapping_suite_sdk.core.models.collection_asset import TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import \
    MappingPackageV3MetadataJSONLD


class MappingPackageV3Lightweight(MappingPackage):
    """
        A class representing a complete V3 (Unified) mapping package configuration.

        This class serves as the root container for all components of a mapping package,
        including metadata, mapping configurations, and various test suites. It provides
        a comprehensive structure for organizing and managing all aspects of a data
        mapping project.
    """

    # Metadata
    metadata: MappingPackageV3MetadataJSONLD = Field(..., description="Package metadata containing general information")

    # Package elements (folders and files)
    technical_mapping_suite: TechnicalMappingCollectionAsset = Field(...,
                                                                     description="All the RML files, which are RMLFragments")
    vocabulary_mapping_suite: VocabularyMappingCollectionAsset = Field(...,
                                                                       description="The resources JSONs, CSV and XML files")