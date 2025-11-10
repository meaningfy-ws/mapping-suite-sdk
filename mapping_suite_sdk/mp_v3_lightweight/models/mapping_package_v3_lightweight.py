from typing import List

from pydantic import Field

from mapping_suite_sdk.core.models.collection_asset import TechnicalMappingCollectionAsset, \
    VocabularyMappingCollectionAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight_metadata_jsonld import \
    MappingPackageV3LightweightMetadataJSONLD


class MappingPackageV3Lightweight(MappingPackage):
    """
       A class representing a lightweight V3 (Unified) mapping package configuration.

        This class serves as the root container for all components of a "lightweight" mapping package,
        including metadata and mapping configurations. As compared to the full, fat or heavyweight
        package, it provides a structure that facilitates the bare minimum necessary for data transformation,
        namely the technical mapping rules and associated vocabulary resources only.
    """

    # Metadata
    metadata: MappingPackageV3LightweightMetadataJSONLD = Field(..., description="Package metadata containing general information")

    # Package elements (folders and files)
    technical_mapping_suite: TechnicalMappingCollectionAsset = Field(...,
                                                                     description="All the RML files, which are RMLFragments")
    vocabulary_mapping_suite: VocabularyMappingCollectionAsset = Field(...,
                                                                       description="The resources JSONs, CSV and XML files")