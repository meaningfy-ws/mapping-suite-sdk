from typing import Optional

from pydantic import Field

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.core.models.pydantic import PydanticModel


class MappingPackageV2EligibilityConstraints(PydanticModel):
    """
        This shall be a generic dict-like structure as the constraints
        in the V2 (eForms) are different from the constraints in the V1 (Standard Forms).
    """
    # TODO: For the moment, no concrete structure is provided
    constraints: dict = Field(default_factory=dict)

    description: Optional[str] = Field(default=None, exclude=True)


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
