from typing import List

from pydantic import Field

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.core.models.pydantic import PydanticModel


class MappingPackageV1Constraints(PydanticModel):
    """

    """

    eforms_subtype: List[int] = Field(..., description="")

    start_date: List[str] = Field(..., description="")

    end_date: List[str] = Field(..., description="")

    min_xsd_version: List[str] = Field(..., description="")

    max_xsd_version: List[str] = Field(..., description="")


class MappingPackageV1EligibilityConstraints(PydanticModel):
    """

    """
    constraints: MappingPackageV1Constraints = Field(..., description="")


class MappingPackageV1Metadata(MappingPackageMetadata):
    """
        A class representing the metadata of mapping package V1 (used in Standard Forms mappings).
    """
    title: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH, max_length=mssdk_config.MSSDK_MAX_STR_LENGTH)
    identifier: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH,
                            max_length=mssdk_config.MSSDK_MAX_STR_LENGTH)
    issue_date: str = Field(..., min_length=mssdk_config.MSSDK_MIN_STR_LENGTH,
                            max_length=mssdk_config.MSSDK_MAX_STR_LENGTH, alias="created_at")
    mapping_version: str = Field(..., description="Version of source data that will be mapped", alias="version")
    ontology_version: str = Field(..., description="Version of target ontology")
    description: str = Field(..., description="Metadata description")

    eligibility_constraints: MappingPackageV1EligibilityConstraints = Field(...,
                                                                            description="Constraints defining package applicability",
                                                                            alias="metadata_constraints")
    signature: str = Field(..., alias="mapping_suite_hash_digest", description="Package integrity hash")
