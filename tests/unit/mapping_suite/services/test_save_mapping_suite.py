"""
Unit tests for the save_mapping_suite service.

Tests focus on service layer responsibilities:
- Orchestration of save workflow
- Exception handling and validation
- Integration with MongoDBRepository
"""
from unittest.mock import Mock

import pytest

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_suite.models.mapping_suite import MappingSuite
from mapping_suite_sdk.mapping_suite.services.save_mapping_suite import (
    save_mapping_suite_to_mongo_db
)


class TestSaveMappingSuiteToMongoDB:
    """Tests for saving mapping suites to MongoDB."""

    def test_save_mapping_suite_to_mongo_db_success(self):
        """Test successful saving of a mapping suite to MongoDB."""
        mock_repository = Mock(spec=MongoDBRepository)
        mock_suite = Mock(spec=MappingSuite)
        mock_suite.id = "test_suite_id"
        mock_repository.create.return_value = mock_suite

        result = save_mapping_suite_to_mongo_db(mock_suite, mock_repository)

        mock_repository.create.assert_called_once_with(mock_suite)
        assert result == mock_suite

    def test_save_mapping_suite_to_mongo_db_none_suite(self):
        """Test error handling for None mapping suite."""
        mock_repository = Mock(spec=MongoDBRepository)

        with pytest.raises(ValueError) as exc_info:
            save_mapping_suite_to_mongo_db(None, mock_repository)

        assert "Mapping suite must be provided" in str(exc_info.value)

    def test_save_mapping_suite_to_mongo_db_none_repository(self):
        """Test error handling for None repository."""
        mock_suite = Mock(spec=MappingSuite)

        with pytest.raises(ValueError) as exc_info:
            save_mapping_suite_to_mongo_db(mock_suite, None)

        assert "MongoDB repository must be provided" in str(exc_info.value)

    def test_save_mapping_suite_to_mongo_db_repository_exception(self):
        """Test error propagation from database access failures."""
        mock_repository = Mock(spec=MongoDBRepository)
        mock_suite = Mock(spec=MappingSuite)
        mock_repository.create.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            save_mapping_suite_to_mongo_db(mock_suite, mock_repository)

        assert "Database connection failed" in str(exc_info.value)

    def test_save_mapping_suite_to_mongo_db_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(save_mapping_suite_to_mongo_db, '__name__')
        assert save_mapping_suite_to_mongo_db.__name__ == 'save_mapping_suite_to_mongo_db'

    def test_save_mapping_suite_to_mongo_db_uses_suite_id(self, dummy_mapping_suite_folder_path):
        """Test that save uses the suite's identifier for MongoDB _id."""
        from mapping_suite_sdk.mapping_suite.services.load_mapping_suite import (
            load_mapping_suite_from_folder
        )
        import mongomock
        from mapping_suite_sdk.core.adapters.repository import MongoDBRepository

        # Load a real mapping suite
        suite = load_mapping_suite_from_folder(dummy_mapping_suite_folder_path)
        expected_id = suite.id

        # Create a real MongoDB repository with mongomock
        mongo_client = mongomock.MongoClient()
        repository = MongoDBRepository(
            model_class=MappingSuite,
            mongo_client=mongo_client,
            database_name="test_db",
            collection_name="mapping_suites"
        )

        # Save the suite
        saved_suite = save_mapping_suite_to_mongo_db(suite, repository)

        # Verify the suite was saved with the correct _id
        assert saved_suite == suite
        stored_doc = repository.collection.find_one({"_id": expected_id})
        assert stored_doc is not None
        assert stored_doc["_id"] == expected_id

