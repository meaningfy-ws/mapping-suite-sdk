import mongomock
import pytest
from pymongo.errors import DuplicateKeyError

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository, ModelNotFoundError
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


def test_read_with_computed_id_property(mongo_client: mongomock.MongoClient, dummy_mapping_package_v1_model):
    """Test read() with a model that has a computed id property (not in model_fields).
    
    This tests the branch where model doesn't have an 'id' field in model_fields,
    but has a computed property (like MappingPackageV1.id).
    """
    from mapping_suite_sdk.mapping_package_v1.models import MappingPackageV1
    
    repository = MongoDBRepository[MappingPackageV1](
        model_class=MappingPackageV1,
        mongo_client=mongo_client,
        database_name="test_db",
        collection_name="mapping_package"
    )
    
    # Create the package
    created_package = repository.create(dummy_mapping_package_v1_model)
    package_id = created_package.id
    
    # Read it back - this should test the branch where _id is removed (not mapped to id)
    read_package = repository.read(package_id)
    
    assert read_package.id == package_id
    assert read_package.metadata.identifier == dummy_mapping_package_v1_model.metadata.identifier


def test_read_many_with_computed_id_property(mongo_client: mongomock.MongoClient, dummy_mapping_package_v1_model):
    """Test read_many() with models that have computed id properties (not in model_fields).
    
    This tests the branch where model doesn't have an 'id' field in model_fields,
    but has a computed property (like MappingPackageV1.id).
    """
    from mapping_suite_sdk.mapping_package_v1.models import MappingPackageV1
    
    repository = MongoDBRepository[MappingPackageV1](
        model_class=MappingPackageV1,
        mongo_client=mongo_client,
        database_name="test_db",
        collection_name="mapping_package"
    )
    
    # Create multiple packages
    package1 = repository.create(dummy_mapping_package_v1_model)
    
    # Create a second package by modifying the identifier
    package2_data = dummy_mapping_package_v1_model.model_copy(deep=True)
    package2_data.metadata.identifier = "package_F23"
    package2 = repository.create(package2_data)
    
    # Read all packages - this should test the branch where _id is removed (not mapped to id)
    all_packages = repository.read_many()
    
    assert len(all_packages) >= 2
    package_ids = {p.id for p in all_packages}
    assert package1.id in package_ids
    assert package2.id in package_ids


def test_read_without_id_field(mongo_client: mongomock.MongoClient, sample_model: TestModel):
    """Test read() when document doesn't have _id field (edge case).
    
    This tests the defensive code path where _id might not be present.
    """
    from unittest.mock import patch
    
    repository = MongoDBRepository[TestModel](
        model_class=TestModel,
        mongo_client=mongo_client,
        database_name="test_db",
        collection_name="test_collection"
    )
    
    # Mock find_one to return a document without _id
    doc_without_id = sample_model.model_dump(by_alias=True, mode="json")
    doc_without_id.pop("_id", None)
    
    with patch.object(repository.collection, 'find_one', return_value=doc_without_id):
        # Read should handle the case where _id is not in the document
        result = repository.read(sample_model.id)
        assert result.name == sample_model.name
        assert result.id == sample_model.id  # Should use the provided id


def test_read_many_without_id_field(mongo_client: mongomock.MongoClient, sample_model: TestModel):
    """Test read_many() when documents don't have _id field (edge case).
    
    This tests the defensive code path where _id might not be present in documents.
    """
    from unittest.mock import patch
    
    repository = MongoDBRepository[TestModel](
        model_class=TestModel,
        mongo_client=mongo_client,
        database_name="test_db",
        collection_name="test_collection"
    )
    
    # Create documents without _id
    doc1 = sample_model.model_dump(by_alias=True, mode="json")
    doc1.pop("_id", None)
    doc1["name"] = "Model Without ID 1"
    
    doc2 = sample_model.model_dump(by_alias=True, mode="json")
    doc2.pop("_id", None)
    doc2["name"] = "Model Without ID 2"
    
    # Mock find to return documents without _id
    with patch.object(repository.collection, 'find', return_value=iter([doc1, doc2])):
        # Read should handle documents without _id
        results = repository.read_many()
        assert len(results) == 2
        names = {r.name for r in results}
        assert "Model Without ID 1" in names
        assert "Model Without ID 2" in names
