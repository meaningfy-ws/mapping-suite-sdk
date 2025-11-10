from typing import Optional, Union, Dict, Any

from pydantic import Field, ConfigDict

from mapping_suite_sdk.core.models.pydantic import PydanticModel


class JSONLDModel(PydanticModel):
    """
    Core model supporting JSON-LD structure.
    Accepts both JSON-LD keys (@id, @type, @context) and plain keys (id, type, context).
    """

    context: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias='@context')
    type: Optional[str] = Field(default=None, alias='@type')
    id: Optional[str] = Field(default=None, alias='@id')

    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow',
        from_attributes=True,
    )
