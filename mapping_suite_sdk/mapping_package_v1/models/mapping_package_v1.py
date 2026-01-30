from pydantic import Field

from mapping_suite_sdk.core.models.mapping_package import MappingPackageCommon
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1_metadata import MappingPackageV1Metadata


class MappingPackageV1(MappingPackageCommon):
    """
        A class representing a complete V1 (used in Standard Forms mappings) mapping package configuration.

        This class serves as the root container for all components of a mapping package,
        including metadata, mapping configurations, and various test suites. It provides
        a comprehensive structure for organizing and managing all aspects of a data
        mapping project.
    """

    metadata: MappingPackageV1Metadata = Field(..., description="Package metadata containing general information")
