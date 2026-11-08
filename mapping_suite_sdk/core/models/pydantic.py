from dataclasses import dataclass
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field


class PydanticModel(BaseModel):
    """
    A base model class providing core configurations for all project-related models.
    """

    object_description: str | None = Field(
        default=None,
        exclude=True,
        description="Optional descriptive text providing additional information about the model instance.",
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        frozen=False,
        arbitrary_types_allowed=False,
        use_enum_values=True,
        str_strip_whitespace=False,
        validate_default=True,
        populate_by_name=True,
        ser_json_bytes="base64",
    )


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
