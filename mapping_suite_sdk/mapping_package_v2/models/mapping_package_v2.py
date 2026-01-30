from pydantic import Field

from mapping_suite_sdk.core.models.mapping_package import MappingPackageCommon
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata


class MappingPackageV2(MappingPackageCommon):
    """
        A class representing a complete V2 (eForms) mapping package configuration.

        This class serves as the root container for all components of a mapping package,
        including metadata, mapping configurations, and various test suites. It provides
        a comprehensive structure for organizing and managing all aspects of a data
        mapping project.
    """

    metadata: MappingPackageV2Metadata = Field(..., description="Package metadata containing general information")
