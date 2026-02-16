from typing import Optional, List

from pydantic import Field

from mapping_suite_sdk.config import mssdk_config
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.core.models.pydantic import PydanticModel


class MappingPackageV2Constraints(PydanticModel):
    """
        A class that defines specific fields of the mapping packages version specific constraints.
    """

    eforms_subtype: List[str] = Field(..., description="")

    start_date: Optional[List[str]] = Field(..., description="")

    end_date: Optional[List[str]] = Field(..., description="")

    eforms_sdk_versions: List[str] = Field(..., description="")


class MappingPackageV2EligibilityConstraints(PydanticModel):
    """
        A class that defines constraints field used in metadata.json
    """
    constraints: MappingPackageV2Constraints = Field(..., description="Fields with mapping package version specific constraints")


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

    metadata_constraints: MappingPackageV2EligibilityConstraints = Field(..., description="Constraints defining package applicability")
    signature: str = Field(..., alias="mapping_suite_hash_digest", description="Package integrity hash")
