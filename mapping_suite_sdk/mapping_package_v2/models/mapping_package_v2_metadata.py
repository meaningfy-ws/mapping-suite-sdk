from typing import Optional, List

from pydantic import Field

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.core.models.pydantic import PydanticModel


class MappingPackageV2Constraints(PydanticModel):
    """

    """

    eforms_subtype: List[str] = Field(..., description="")

    start_date: Optional[List[str]] = Field(..., description="")

    end_date: Optional[List[str]] = Field(..., description="")

    eforms_sdk_versions: List[str] = Field(..., description="")


class MappingPackageV2EligibilityConstraints(PydanticModel):
    """

    """
    constraints: MappingPackageV2Constraints = Field(..., description="")


class MappingPackageV2Metadata(MappingPackageMetadata):
    """
        A class representing the metadata of eForms specific mapping package.
    """
    identifier: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH,
                            max_length=mssdk_config.MSSDK_MAX_STR_LENGTH)
    title: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH, max_length=mssdk_config.MSSDK_MAX_STR_LENGTH)
    issue_date: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH,
                            max_length=mssdk_config.MSSDK_MAX_STR_LENGTH, alias="created_at")
    description: str = Field(..., description="Metadata description")
    mapping_version: str = Field(..., description="Version of source data that will be mapped")
    ontology_version: str = Field(..., description="Version of target ontology")
    type: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH, max_length=mssdk_config.MSSDK_MAX_STR_LENGTH,
                      alias="mapping_type")

    eligibility_constraints: MappingPackageV2EligibilityConstraints = Field(...,
                                                                            description="Constraints defining package applicability",
                                                                            alias="metadata_constraints")
    signature: str = Field(..., alias="mapping_suite_hash_digest", description="Package integrity hash")
