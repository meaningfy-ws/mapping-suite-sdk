import hashlib
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, model_validator

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

    description: Optional[str] = Field(
        default=None,
        description="Optional descriptive text providing additional information about the model instance."
    )

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
        smart_union = True
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
