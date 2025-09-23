from pathlib import Path

from pydantic import Field

from mapping_suite_sdk.core.models.pydantic import PydanticModel


class MappingPackageMetadata(PydanticModel):
    """
        A class representing the general metadata of mapping package.
    """
    path: Path = Field(..., description="Path within a mapping package")
