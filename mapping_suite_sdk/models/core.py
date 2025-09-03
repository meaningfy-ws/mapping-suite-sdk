import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, TypeVar, cast, Dict

from pydantic import BaseModel, Field, model_validator, AliasChoices, PrivateAttr

MSSDK_STR_MIN_LENGTH = 1
MSSDK_STR_MAX_LENGTH = 256
MSSDK_DEFAULT_STR_ENCODE = 'utf-8'


class CoreModel(BaseModel):
    """A base model class providing core functionality for all mapping-related models."""

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

    # Tracks aliases that were actually used during deserialization.
    _original_keys: Dict[str, str] = PrivateAttr(default={})

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        instance = super().model_validate(obj, **kwargs)

        # If created from dict/JSON, record which aliases were actually used
        if isinstance(obj, dict):
            original_keys = {}
            for field_name, field_info in cls.model_fields.items():
                if hasattr(field_info, 'validation_alias') and isinstance(field_info.validation_alias, AliasChoices):
                    for alias in field_info.validation_alias.choices:
                        if alias in obj:
                            original_keys[field_name] = alias
                            break

            instance._original_keys = original_keys

        return instance

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)

        # Use tracked keys from deserialization, or fall back to field names
        result = {}
        for field_name, value in data.items():
            key_to_use = self._original_keys.get(field_name, field_name)
            result[key_to_use] = value

        return result

    @model_validator(mode='after')
    def generate_id(self) -> 'CoreModel':
        """Generate a unique ID based on the model data, excluding validation info."""
        if self.id is None:
            model_data = self.model_dump(exclude={'id'}, exclude_none=False, exclude_unset=False, mode='json')
            data_string = json.dumps(model_data, sort_keys=True)
            hash_value = hashlib.sha256(data_string.encode(MSSDK_DEFAULT_STR_ENCODE)).hexdigest()
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


TModel = TypeVar("TModel", bound=BaseModel)


def fields(model: type[TModel], /) -> TModel:
    return cast(TModel, _GetFields(model))
