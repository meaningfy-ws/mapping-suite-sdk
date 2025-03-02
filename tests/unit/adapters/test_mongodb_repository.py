import mongomock
import pytest
from pymongo.errors import DuplicateKeyError

from mapping_suite_sdk.adapters.repository import MongoDBRepository, ModelNotFoundError
from tests.conftest import TestModel


def test_create_with_success_non_existing_element(dummy_mongo_repository: MongoDBRepository, sample_model: TestModel):
    result = dummy_mongo_repository.create(sample_model)
    stored_result = dummy_mongo_repository.collection.find_one({"_id": sample_model.id})

    assert result == sample_model
    assert stored_result is not None
    stored_model = TestModel.model_validate(stored_result)

    assert stored_model == sample_model


def test_create_fails_on_creating_existing_element(dummy_mongo_repository: MongoDBRepository, sample_model: TestModel):
    dummy_mongo_repository.create(sample_model)

    with pytest.raises(DuplicateKeyError):
        dummy_mongo_repository.create(sample_model)


def test_read_with_success_existing_element(dummy_mongo_repository: MongoDBRepository, sample_model: TestModel):
    dummy_mongo_repository.create(sample_model)

    stored_model = dummy_mongo_repository.read(sample_model.id)

    assert stored_model is not None
    assert stored_model == sample_model
    assert stored_model.id == sample_model.id


def test_read_fails_on_non_existing_element(dummy_mongo_repository: MongoDBRepository, sample_model: TestModel):
    with pytest.raises(ModelNotFoundError):
        dummy_mongo_repository.read(sample_model.id)


def test_read_many_with_success_without_filters(dummy_mongo_repository: MongoDBRepository):
    models = [
        TestModel(id="test1", name="Model 1", count=1),
        TestModel(id="test2", name="Model 2", count=2),
        TestModel(id="test3", name="Model 3", count=3)
    ]
    for model in models:
        dummy_mongo_repository.create(model)

    results = dummy_mongo_repository.read_many()

    assert len(results) == 3
    assert {model.id for model in results} == {"test1", "test2", "test3"}


def test_read_many_with_success_with_filters(dummy_mongo_repository: MongoDBRepository):
    models = [
        TestModel(id="test1", name="Model 1", count=1),
        TestModel(id="test2", name="Model 2", count=2),
        TestModel(id="test3", name="Model 2", count=3)  # Note: same name as test2
    ]
    for model in models:
        dummy_mongo_repository.create(model)

    results = dummy_mongo_repository.read_many({"name": "Model 2"})

    assert len(results) == 2
    assert {model.id for model in results} == {"test2", "test3"}


def test_update_with_success_existing_element(dummy_mongo_repository: MongoDBRepository,
                                              sample_model: TestModel,
                                              updated_sample_model: TestModel):
    dummy_mongo_repository.create(sample_model)
    result = dummy_mongo_repository.update(updated_sample_model)

    assert result == updated_sample_model
    stored_model = TestModel.model_validate(
        dummy_mongo_repository.collection.find_one({"_id": updated_sample_model.id}))
    assert stored_model == updated_sample_model
    assert stored_model != sample_model


def test_update_with_fails_on_non_existing_element(dummy_mongo_repository: MongoDBRepository,
                                                   sample_model: TestModel,
                                                   updated_sample_model: TestModel):
    with pytest.raises(ModelNotFoundError):
        dummy_mongo_repository.update(updated_sample_model)


def test_delete_with_success_existing_element(dummy_mongo_repository: MongoDBRepository, sample_model: TestModel):
    result = dummy_mongo_repository.create(sample_model)
    stored_result = dummy_mongo_repository.collection.find_one({"_id": sample_model.id})

    assert result == sample_model
    assert stored_result is not None

    dummy_mongo_repository.delete(sample_model.id)

    assert dummy_mongo_repository.collection.find_one({"_id": sample_model.id}) is None


def test_delete_fails_on_non_existing_element(dummy_mongo_repository: MongoDBRepository, sample_model: TestModel):
    with pytest.raises(ModelNotFoundError):
        dummy_mongo_repository.delete(sample_model.id)


def test_repository_use_collection_name_from_model_class(mongo_client: mongomock.MongoClient, dummy_database_name: str):
    repository = MongoDBRepository(
        model_class=TestModel,
        mongo_client=mongo_client,
        database_name=dummy_database_name
    )

    assert repository.collection_name == TestModel.__name__


def test_repository_use_custom_collection_name(mongo_client: mongomock.MongoClient,
                                               dummy_database_name: str,
                                               dummy_collection_name: str):
    repository = MongoDBRepository(
        model_class=TestModel,
        mongo_client=mongo_client,
        database_name=dummy_database_name,
        collection_name=dummy_collection_name
    )

    assert repository.collection_name == dummy_collection_name
