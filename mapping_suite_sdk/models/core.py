from typing import Optional

from pydantic import BaseModel, Field

MSSDK_STR_MIN_LENGTH = 1
MSSDK_STR_MAX_LENGTH = 256
MSSDK_DEFAULT_STR_ENCODE = 'utf-8'


class CoreModel(BaseModel):
    """A base model class providing core functionality for all mapping-related models.

    This class extends Pydantic's BaseModel to provide common attributes and configuration
    settings used across all mapping models. It implements strict validation rules to
    ensure data integrity and consistency across all mapping components.
    """

    description: Optional[str] = Field(default=None,
                                       description="Optional descriptive text providing additional information about the model instance.")

    class Config:
        validate_assignment = True
        extra = "forbid"  # Forbids extra attributes
        allow_mutation = False  # Makes instances immutable
        frozen = True  # Alternative way to make instances immutable
        validate_all = True  # Validates default values
        arbitrary_types_allowed = False  # Strict type checking
        smart_union = True  # Better Union type handling
        use_enum_values = True  # Use enum values instead of members
        str_strip_whitespace = False  # Strips whitespace from strings
        validate_default = True  # Validates default values
        val_json_bytes = 'base64'
        ser_json_bytes = 'base64'
        populate_by_name = True
        serialize_by_alias = True