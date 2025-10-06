import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, TypeVar, cast

from pydantic import BaseModel, Field, model_validator

from mapping_suite_sdk import mssdk_config


class PydanticModel(BaseModel):
    """
        A base model class providing core configurations for all project-related models.
    """

    id: Optional[str] = Field(
        default=None,
        alias="_id",
        exclude=True,
        description="Unique identifier for the model instance, automatically generated."
    )

    object_description: Optional[str] = Field(
        default=None,
        exclude=True,
        description="Optional descriptive text providing additional information about the model instance."
    )

    @model_validator(mode='after')
    def generate_id(self) -> 'PydanticModel':
        """Generate a unique ID based on the model data, excluding validation info."""
        if self.id is None:
            model_data = self.model_dump(exclude={'id'}, exclude_none=False, exclude_unset=False, mode='json')
            data_string = json.dumps(model_data, sort_keys=True)
            hash_value = hashlib.sha256(data_string.encode(mssdk_config.MSSDK_DEFAULT_STR_ENCODE)).hexdigest()
            object.__setattr__(self, 'id', hash_value)
        return self

    class Config:
        validate_assignment = True
        extra = "forbid"
        frozen = False
        arbitrary_types_allowed = False
        use_enum_values = True
        str_strip_whitespace = False
        validate_default = True
        val_json_bytes = 'base64'
        ser_json_bytes = 'base64'
        populate_by_name = True
        serialize_by_alias = True
        json_encoders = {
            Path: str
        }


# Solution to access Pydantic fields as Class properties so that no need to hardcode field names
# Example: model_dump(exclude={fields(MappingPackageMetadata).signature}))
# Example with hardcode: model_dump(exclude={"signature"}))
# See: https://github.com/pydantic/pydantic/discussions/8600
@dataclass(frozen=True)
class _GetFields:
    _model: type[BaseModel]

    def __getattr__(self, item: str) -> Any:
        if item in self._model.model_fields:
            return item

        return getattr(self._model, item)


TModel = TypeVar("TModel", bound=PydanticModel)


def fields(model: type[TModel], /) -> TModel:
    return cast(TModel, _GetFields(model))
