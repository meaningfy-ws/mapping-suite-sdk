from typing import Optional

from pydantic import Field

from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.core.models.pydantic import PydanticModel
from mapping_suite_sdk.vars import MSSDK_STR_MIN_LENGTH, MSSDK_STR_MAX_LENGTH


class MappingPackageV1EligibilityConstraints(PydanticModel):
    """
        This shall be a generic dict-like structure as the constraints
        in the V2 (used in eForms mappings) are different from the
        constraints in the V1 (used in Standard Forms mappings).
    """
    # TODO: For the moment, no concrete structure is provided
    constraints: dict = Field(default_factory=dict)

    description: Optional[str] = Field(default=None, exclude=True)


class MappingPackageV1Metadata(MappingPackageMetadata):
    """
        A class representing the metadata of mapping package V1 (used in Standard Forms mappings).
    """
    title: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH)
    identifier: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH)
    issue_date: str = Field(..., min_length=MSSDK_STR_MIN_LENGTH, max_length=MSSDK_STR_MAX_LENGTH, alias="created_at")
    mapping_version: str = Field(..., description="Version of source data that will be mapped", alias="version")
    ontology_version: str = Field(..., description="Version of target ontology")
    description: str = Field(..., description="Metadata description")
    eligibility_constraints: MappingPackageV1EligibilityConstraints = Field(...,
                                                                            description="Constraints defining package applicability",
                                                                            alias="metadata_constraints")
    signature: str = Field(..., alias="mapping_suite_hash_digest", description="Package integrity hash")