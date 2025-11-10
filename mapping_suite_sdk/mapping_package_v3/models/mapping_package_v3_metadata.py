from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict, Field, RootModel

metamodel_version = "None"
version = "0.1.0"


from mapping_suite_sdk.core.models.pydantic import PydanticModel


class ConfiguredBaseModel(PydanticModel):
    pass


class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key: str):
        return getattr(self.root, key)

    def __getitem__(self, key: str):
        return self.root[key]

    def __setitem__(self, key: str, value):
        self.root[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.root


linkml_meta = None


class MappingPackageV3Metadata(ConfiguredBaseModel):
    """
    Metadata for a data transformation rules package
    """

    id: str = Field(default=..., description="""Unique identifier of the package""")
    title: str = Field(
        default=..., description="""Human-readable name of the package"""
    )
    project_identifier: str = Field(
        default=...,
        description="""Name or identifier of the data transformation project""",
    )
    created_at: datetime = Field(
        default=...,
        description="""Timestamp of when the package/metadata was created""",
    )
    mapping_version: str = Field(
        default=...,
        description="""Version of the transformation rules in the package""",
    )
    model_version: str = Field(
        default=..., description="""Version of the ontology this mapping aligns with"""
    )
    description: Optional[str] = Field(
        default=None,
        description="""A brief summary of what the package represents or maps.""",
    )
    applicability_constraints: Optional[ApplicabilityConstraints] = Field(
        default=None,
        description="""Applicability constraints for when and where mapping rules of the package are valid""",
    )
    mapping_suite_hash_digest: str = Field(
        default=...,
        description="""Cryptographic hash of the mapping package for integrity verification""",
    )


class ApplicabilityConstraints(ConfiguredBaseModel):
    """
    Container for constraint types
    """

    document_type_list: list[str] = Field(
        default=..., description="""List of applicable document type identifiers"""
    )
    document_time_interval: Optional[DateTimeInterval] = Field(
        default=None,
        description="""Interval of starting and ending document datetime""",
    )
    document_version_list: Optional[list[str]] = Field(
        default=None, description="""List of supported document versions"""
    )
    document_version_range: Optional[VersionRange] = Field(
        default=None,
        description="""Range of (minimum and maximum) supported document versions""",
    )


class VersionRange(ConfiguredBaseModel):
    """
    Container for minimum and maximum version values
    """

    min: Optional[str] = Field(
        default=None, description="""Minimum supported document version"""
    )
    max: Optional[str] = Field(
        default=None, description="""Maximum supported document version"""
    )


class DateTimeInterval(ConfiguredBaseModel):
    """
    Container for starting and ending datetime values
    """

    start: Optional[datetime] = Field(
        default=None, description="""Earliest applicable datetime for the mapping"""
    )
    end: Optional[datetime] = Field(
        default=None, description="""Latest applicable datetime for the mapping"""
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
MappingPackageV3Metadata.model_rebuild()
ApplicabilityConstraints.model_rebuild()
VersionRange.model_rebuild()
DateTimeInterval.model_rebuild()
