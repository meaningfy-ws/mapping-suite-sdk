from pydantic import Field

from mapping_suite_sdk.core.models.mapping_package import MappingPackageCommon
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import \
    MappingPackageV3MetadataJSONLD


class MappingPackageV3(MappingPackageCommon):
    """
        A class representing a complete V3 (Unified) mapping package configuration.

        This class serves as the root container for all components of a mapping package,
        including metadata, mapping configurations, and various test suites. It provides
        a comprehensive structure for organizing and managing all aspects of a data
        mapping project.
    """

    metadata: MappingPackageV3MetadataJSONLD = Field(..., description="Package metadata containing general information")
