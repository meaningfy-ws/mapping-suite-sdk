"""
Unit tests for PackageRepository GridFS interception.

Uses unittest.mock only (no mongomock). Mongo client, database, and
collection are mocked; GridFS store helpers are patched so tests do not
require a real MongoDB or GridFS.
"""
import pytest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from pydantic import BaseModel

from mapping_suite_sdk.core.adapters.gridfs_repository import GridFSPackageRepository
from mapping_suite_sdk.core.adapters.package_repository import PackageRepository
from mapping_suite_sdk.core.adapters.repository import ModelNotFoundError
from tests.conftest import TestModel


class ModelWithoutId(BaseModel):
    """Minimal Pydantic model without id/_id for covering read/read_many else branches."""

    name: str
    count: int = 0


def _make_mock_collection():
    """Collection mock that stores documents in a dict for find_one/insert_one/etc."""
    store = {}

    def insert_one(doc):
        store[doc["_id"]] = dict(doc)

    def find_one(query):
        if "_id" in query:
            return store.get(query["_id"])
        return None

    def replace_one(query, doc):
        if query.get("_id") in store:
            store[query["_id"]] = dict(doc)

    def delete_one(query):
        key = query.get("_id")
        if key in store:
            del store[key]
            return MagicMock(deleted_count=1)
        return MagicMock(deleted_count=0)

    def find(query):
        return list(store.values())

    coll = MagicMock()
    coll.insert_one.side_effect = insert_one
    coll.find_one.side_effect = find_one
    coll.replace_one.side_effect = replace_one
    coll.delete_one.side_effect = delete_one
    coll.find.side_effect = find
    return coll


def _make_repository(collection=None, model_class=TestModel):
    if collection is None:
        collection = _make_mock_collection()
    db = MagicMock()
    db.__getitem__.return_value = collection
    client = MagicMock()
    client.__getitem__.return_value = db
    return PackageRepository(
        model_class=model_class,
        mongo_client=client,
        database_name="test_db",
        collection_name="test_coll",
        gridfs_threshold_bytes=100,
        gridfs_bucket_name="test_bucket",
    )


class TestPackageRepositoryGridFSInterceptionCreate:
    """Tests for PackageRepository.create (GridFS interception)."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.prepare_doc_for_insert")
    def test_create_calls_prepare_then_insert(self, mock_prepare):
        repo = _make_repository()
        model = TestModel(id="id1", name="n", description="d", count=1)
        mock_prepare.assert_not_called()
        result = repo.create(model)
        assert result == model
        mock_prepare.assert_called_once()
        call_args = mock_prepare.call_args[0]
        assert call_args[0]["_id"] == "id1"
        assert call_args[1] == repo.database
        assert repo.collection.find_one({"_id": "id1"}) is not None


class TestPackageRepositoryGridFSInterceptionRead:
    """Tests for PackageRepository.read (GridFS interception)."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.resolve_doc_gridfs_refs")
    def test_read_resolves_refs_and_returns_model(self, mock_resolve):
        coll = _make_mock_collection()
        doc = {"_id": "id1", "name": "n", "description": "d", "count": 1}
        coll.insert_one(doc)
        repo = _make_repository(collection=coll)
        mock_resolve.assert_not_called()
        result = repo.read("id1")
        mock_resolve.assert_called_once()
        assert result.id == "id1"
        assert result.name == "n"

    def test_read_raises_when_not_found(self):
        repo = _make_repository()
        with pytest.raises(ModelNotFoundError, match="id_missing"):
            repo.read("id_missing")

    @patch("mapping_suite_sdk.core.adapters.package_repository.resolve_doc_gridfs_refs")
    def test_read_pops_id_when_model_has_no_id_field(self, mock_resolve):
        """Covers the else branch: model has no id field → result_dict.pop('_id')."""
        coll = _make_mock_collection()
        coll.insert_one({"_id": "x", "name": "n", "count": 1})
        repo = _make_repository(collection=coll, model_class=ModelWithoutId)
        result = repo.read("x")
        assert result.name == "n"
        assert result.count == 1
        # model_validate was called with dict without _id (else branch ran)
        mock_resolve.assert_called_once()


class TestPackageRepositoryGridFSInterceptionReadMany:
    """Tests for PackageRepository.read_many (GridFS interception)."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.resolve_doc_gridfs_refs")
    def test_read_many_resolves_refs_and_returns_models(self, mock_resolve):
        coll = _make_mock_collection()
        coll.insert_one({"_id": "a", "name": "A", "description": None, "count": 0})
        coll.insert_one({"_id": "b", "name": "B", "description": None, "count": 0})
        repo = _make_repository(collection=coll)
        results = repo.read_many()
        assert len(results) == 2
        assert mock_resolve.call_count == 2
        ids = {r.id for r in results}
        assert ids == {"a", "b"}

    @patch("mapping_suite_sdk.core.adapters.package_repository.resolve_doc_gridfs_refs")
    def test_read_many_pops_id_when_model_has_no_id_field(self, mock_resolve):
        """Covers read_many else branch: model has no id → doc_dict.pop('_id')."""
        coll = _make_mock_collection()
        coll.insert_one({"_id": "a", "name": "A", "count": 0})
        coll.insert_one({"_id": "b", "name": "B", "count": 1})
        repo = _make_repository(collection=coll, model_class=ModelWithoutId)
        results = repo.read_many()
        assert len(results) == 2
        names = {r.name for r in results}
        assert names == {"A", "B"}
        assert mock_resolve.call_count == 2


class TestPackageRepositoryGridFSInterceptionUpdate:
    """Tests for PackageRepository.update (GridFS interception)."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.delete_content")
    @patch("mapping_suite_sdk.core.adapters.package_repository.prepare_doc_for_insert")
    @patch("mapping_suite_sdk.core.adapters.package_repository.collect_gridfs_ids_from_doc")
    def test_update_replaces_doc_and_deletes_old_gridfs(
        self, mock_collect, mock_prepare, mock_delete
    ):
        mock_collect.return_value = []
        coll = _make_mock_collection()
        coll.insert_one({"_id": "id1", "name": "old", "description": None, "count": 0})
        repo = _make_repository(collection=coll)
        updated = TestModel(id="id1", name="new", description="d", count=2)
        result = repo.update(updated)
        assert result == updated
        mock_prepare.assert_called_once()
        mock_collect.assert_called()
        stored = coll.find_one({"_id": "id1"})
        assert stored is not None
        assert stored["name"] == "new"

    @patch("mapping_suite_sdk.core.adapters.package_repository.delete_content")
    @patch("mapping_suite_sdk.core.adapters.package_repository.prepare_doc_for_insert")
    @patch("mapping_suite_sdk.core.adapters.package_repository.collect_gridfs_ids_from_doc")
    def test_update_deletes_old_gridfs_content(
        self, mock_collect, mock_prepare, mock_delete
    ):
        """Covers the loop: for oid in old_gridfs_ids: delete_content(...)."""
        old_oid = ObjectId()
        mock_collect.return_value = [old_oid]
        coll = _make_mock_collection()
        coll.insert_one({"_id": "id1", "name": "old", "description": None, "count": 0})
        repo = _make_repository(collection=coll)
        updated = TestModel(id="id1", name="new", description="d", count=2)
        repo.update(updated)
        mock_delete.assert_called_once()
        args, kwargs = mock_delete.call_args
        assert args[1] == old_oid
        assert kwargs.get("bucket_name") == "test_bucket"

    def test_update_raises_when_not_found(self):
        repo = _make_repository()
        model = TestModel(id="nonexistent", name="n", description="d", count=1)
        with pytest.raises(ModelNotFoundError, match="nonexistent"):
            repo.update(model)


class TestPackageRepositoryGridFSInterceptionDelete:
    """Tests for PackageRepository.delete (GridFS interception)."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.delete_content")
    @patch("mapping_suite_sdk.core.adapters.package_repository.collect_gridfs_ids_from_doc")
    def test_delete_removes_doc_and_calls_delete_content(
        self, mock_collect, mock_delete
    ):
        mock_collect.return_value = []
        coll = _make_mock_collection()
        coll.insert_one({"_id": "id1", "name": "n", "description": None, "count": 0})
        repo = _make_repository(collection=coll)
        repo.delete("id1")
        assert coll.find_one({"_id": "id1"}) is None
        mock_collect.assert_called_once()
        mock_delete.assert_not_called()  # no gridfs ids in this doc

    @patch("mapping_suite_sdk.core.adapters.package_repository.delete_content")
    @patch("mapping_suite_sdk.core.adapters.package_repository.collect_gridfs_ids_from_doc")
    def test_delete_deletes_gridfs_content(self, mock_collect, mock_delete):
        """Covers the loop: for oid in gridfs_ids: delete_content(...)."""
        gridfs_oid = ObjectId()
        mock_collect.return_value = [gridfs_oid]
        coll = _make_mock_collection()
        coll.insert_one({"_id": "id1", "name": "n", "description": None, "count": 0})
        repo = _make_repository(collection=coll)
        repo.delete("id1")
        assert coll.find_one({"_id": "id1"}) is None
        mock_delete.assert_called_once()
        args, kwargs = mock_delete.call_args
        assert args[1] == gridfs_oid
        assert kwargs.get("bucket_name") == "test_bucket"

    def test_delete_raises_when_not_found(self):
        repo = _make_repository()
        with pytest.raises(ModelNotFoundError, match="id_missing"):
            repo.delete("id_missing")


class TestPackageRepositoryCreatePackage:
    """Test that PackageRepository.create_package (convenience method) delegates to create."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.prepare_doc_for_insert")
    def test_create_package_returns_same_as_create(self, mock_prepare):
        repo = _make_repository()  # PackageRepository, which defines create_package
        model = TestModel(id="pkg1", name="p", description="pkg", count=1)
        result = repo.create_package(model)
        assert result == model
        assert repo.collection.find_one({"_id": "pkg1"}) is not None


class TestGridFSPackageRepositoryDeprecated:
    """Tests for deprecated GridFSPackageRepository (alias; coverage for deprecation path)."""

    @patch("mapping_suite_sdk.core.adapters.package_repository.prepare_doc_for_insert")
    def test_init_emits_deprecation_warning(self, mock_prepare):
        with pytest.warns(DeprecationWarning, match="GridFSPackageRepository is deprecated"):
            coll = _make_mock_collection()
            db = MagicMock()
            db.__getitem__.return_value = coll
            client = MagicMock()
            client.__getitem__.return_value = db
            GridFSPackageRepository(
                model_class=TestModel,
                mongo_client=client,
                database_name="test_db",
                collection_name="test_coll",
            )

    @patch("mapping_suite_sdk.core.adapters.package_repository.prepare_doc_for_insert")
    def test_repo_works_like_package_repository(self, mock_prepare):
        with pytest.warns(DeprecationWarning):
            coll = _make_mock_collection()
            db = MagicMock()
            db.__getitem__.return_value = coll
            client = MagicMock()
            client.__getitem__.return_value = db
            repo = GridFSPackageRepository(
                model_class=TestModel,
                mongo_client=client,
                database_name="test_db",
                collection_name="test_coll",
            )
        model = TestModel(id="dep1", name="n", description="d", count=1)
        result = repo.create(model)
        assert result == model
        assert repo.collection.find_one({"_id": "dep1"}) is not None
        got = repo.read("dep1")
        assert got.id == "dep1"
        assert got.name == "n"
