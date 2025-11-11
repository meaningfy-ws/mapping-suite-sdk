from mapping_suite_sdk.core.models.pydantic import fields
from tests.conftest import TestModel


def test_core_model_has_same_id_on_changing_fields(sample_model: TestModel):
    another_model: TestModel = sample_model.model_copy()

    assert sample_model == another_model
    assert sample_model.id == another_model.id

    another_model.name = "another_name"

    assert sample_model != another_model
    assert sample_model.id == another_model.id


def test_fields_helper_returns_field_names():
    """Test that fields() helper returns field names as strings."""
    # Test accessing field names
    assert fields(TestModel).id == "id"
    assert fields(TestModel).name == "name"


def test_fields_helper_accesses_class_attributes():
    """Test that fields() helper can access non-field class attributes."""
    # This tests the fallback getattr on line 66
    # Accessing model_config which is a class attribute, not a field
    config = fields(TestModel).model_config
    assert config is not None
    assert isinstance(config, dict)
    assert config.get("validate_assignment") is True
