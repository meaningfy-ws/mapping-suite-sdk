from tests.conftest import TestModel


def test_core_model_has_same_id_on_changing_fields(sample_model: TestModel):
    another_model: TestModel = sample_model.model_copy()

    assert sample_model == another_model
    assert sample_model.id == another_model.id

    another_model.name = "another_name"

    assert sample_model != another_model
    assert sample_model.id == another_model.id
