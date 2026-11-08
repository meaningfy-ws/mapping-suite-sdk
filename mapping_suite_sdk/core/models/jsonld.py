from typing import Any

from pydantic import ConfigDict, Field

from mapping_suite_sdk.core.models.pydantic import PydanticModel


class JSONLDModel(PydanticModel):
    """
    Core model supporting JSON-LD structure.
    Accepts both JSON-LD keys (@id, @type, @context) and plain keys (id, type, context).
    """

    context: dict[str, Any] | str = Field(default=None, alias="@context")
    type: str | None = Field(default=None, alias="@type")
    id: str | None = Field(default=None, alias="@id")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        from_attributes=True,
    )
