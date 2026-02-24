"""
Unit tests for GridFS store helpers.

Uses unittest.mock only (no mongomock). GridFS/database interactions
are mocked so tests do not require a real MongoDB.
"""
import pytest
from bson import ObjectId
from unittest.mock import MagicMock, patch

# Fake type used so isinstance(db, FakeDatabase) is True when we patch Database with it
class FakeDatabase:
    """Dummy type for patching pymongo.database.Database in tests."""

from mapping_suite_sdk.core.adapters.gridfs_store import (
    GRIDFS_REF_KEY,
    DEFAULT_GRIDFS_THRESHOLD_BYTES,
    collect_gridfs_ids_from_doc,
    prepare_doc_for_insert,
    resolve_doc_gridfs_refs,
    store_content,
    get_content,
    delete_content,
    get_gridfs_bucket,
)


class TestGetGridfsBucket:
    """Tests for get_gridfs_bucket (covers return GridFS(...) line)."""

    def test_returns_gridfs_for_database_and_bucket(self):
        db = MagicMock()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.GridFS"
        ) as mock_gridfs:
            sentinel = object()
            mock_gridfs.return_value = sentinel
            result = get_gridfs_bucket(db, bucket_name="my_bucket")
            mock_gridfs.assert_called_once_with(db, collection="my_bucket")
            assert result is sentinel


class TestCollectGridfsIdsFromDoc:
    """Tests for collect_gridfs_ids_from_doc (pure function, no DB)."""

    def test_collects_single_ref(self):
        oid = ObjectId()
        doc = {"content": {GRIDFS_REF_KEY: oid}}
        assert collect_gridfs_ids_from_doc(doc) == [oid]

    def test_collects_nested_refs(self):
        oid1, oid2 = ObjectId(), ObjectId()
        doc = {
            "files": [
                {"content": {GRIDFS_REF_KEY: oid1}},
                {"content": {GRIDFS_REF_KEY: oid2}},
            ]
        }
        result = collect_gridfs_ids_from_doc(doc)
        assert set(result) == {oid1, oid2}

    def test_ignores_inline_content(self):
        doc = {"content": "small string", "other": {"content": b"bytes"}}
        assert collect_gridfs_ids_from_doc(doc) == []

    def test_empty_doc(self):
        assert collect_gridfs_ids_from_doc({}) == []


class TestPrepareDocForInsert:
    """Tests for prepare_doc_for_insert with mocked store_content."""

    def test_leaves_small_content_unchanged(self):
        doc = {"content": "small"}
        db = MagicMock()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.store_content"
        ) as mock_store:
            prepare_doc_for_insert(
                doc, db, threshold_bytes=100, bucket_name="test_bucket"
            )
        assert doc["content"] == "small"
        mock_store.assert_not_called()

    def test_leaves_small_content_unchanged_with_real_database_type(self):
        """Covers else-branch in _serialize_content_to_gridfs (leave as-is when size < threshold)."""
        doc = {"content": "small"}
        db = FakeDatabase()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.store_content"
        ) as mock_store, patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ):
            prepare_doc_for_insert(
                doc, db, threshold_bytes=100, bucket_name="test_bucket"
            )
        assert doc["content"] == "small"
        mock_store.assert_not_called()

    def test_skips_replacement_when_database_not_pymongo(self):
        """With non-PyMongo database (e.g. mongomock), no GridFS; content left inline."""
        doc = {"content": "x" * 200}
        db = MagicMock()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.store_content"
        ) as mock_store:
            prepare_doc_for_insert(
                doc, db, threshold_bytes=100, bucket_name="test_bucket"
            )
        assert doc["content"] == "x" * 200
        mock_store.assert_not_called()

    def test_replaces_large_content_with_ref(self):
        doc = {"content": "x" * 200}
        db = FakeDatabase()
        fake_id = ObjectId()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.store_content",
            return_value=fake_id,
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ):
            prepare_doc_for_insert(
                doc, db, threshold_bytes=100, bucket_name="test_bucket"
            )
        assert doc["content"] == {GRIDFS_REF_KEY: fake_id}

    def test_nested_large_content_replaced(self):
        doc = {"files": [{"path": "a", "content": "y" * 200}]}
        db = FakeDatabase()
        fake_id = ObjectId()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.store_content",
            return_value=fake_id,
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ):
            prepare_doc_for_insert(
                doc, db, threshold_bytes=100, bucket_name="test_bucket"
            )
        assert doc["files"][0]["content"] == {GRIDFS_REF_KEY: fake_id}

    def test_bytes_content_above_threshold_replaced(self):
        doc = {"content": b"z" * 200}
        db = FakeDatabase()
        fake_id = ObjectId()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.store_content",
            return_value=fake_id,
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ):
            prepare_doc_for_insert(
                doc, db, threshold_bytes=100, bucket_name="test_bucket"
            )
        assert doc["content"] == {GRIDFS_REF_KEY: fake_id}


class TestResolveDocGridfsRefs:
    """Tests for resolve_doc_gridfs_refs with mocked get_content."""

    def test_leaves_inline_content_unchanged(self):
        doc = {"content": "already inline"}
        db = MagicMock()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_content"
        ) as mock_get:
            resolve_doc_gridfs_refs(doc, db, bucket_name="test_bucket")
        assert doc["content"] == "already inline"
        mock_get.assert_not_called()

    def test_skips_resolve_when_database_not_pymongo(self):
        """With non-PyMongo database, refs are left as-is (e.g. mongomock path)."""
        oid = ObjectId()
        doc = {"content": {GRIDFS_REF_KEY: oid}}
        db = MagicMock()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_content"
        ) as mock_get:
            resolve_doc_gridfs_refs(doc, db, bucket_name="test_bucket")
        assert doc["content"] == {GRIDFS_REF_KEY: oid}
        mock_get.assert_not_called()

    def test_resolves_single_ref(self):
        oid = ObjectId()
        doc = {"content": {GRIDFS_REF_KEY: oid}}
        db = FakeDatabase()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_content",
            return_value="resolved text",
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ):
            resolve_doc_gridfs_refs(doc, db, bucket_name="test_bucket")
        assert doc["content"] == "resolved text"

    def test_resolves_nested_refs(self):
        oid1, oid2 = ObjectId(), ObjectId()
        doc = {
            "files": [
                {"content": {GRIDFS_REF_KEY: oid1}},
                {"content": {GRIDFS_REF_KEY: oid2}},
            ]
        }
        db = FakeDatabase()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_content",
            side_effect=["first", "second"],
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ):
            resolve_doc_gridfs_refs(doc, db, bucket_name="test_bucket")
        assert doc["files"][0]["content"] == "first"
        assert doc["files"][1]["content"] == "second"


class TestStoreContent:
    """Tests for store_content with mocked GridFS."""

    def test_store_string_returns_object_id(self):
        db = MagicMock()
        fake_id = ObjectId()
        mock_fs = MagicMock()
        mock_fs.put.return_value = fake_id
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket",
            return_value=mock_fs,
        ):
            result = store_content(db, "hello", bucket_name="test_bucket")
        assert result == fake_id
        mock_fs.put.assert_called_once()
        args = mock_fs.put.call_args
        assert args[0][0] == b"hello"
        assert args[1]["metadata"].get("encoding") == "utf-8"

    def test_store_bytes_no_encoding_metadata(self):
        db = MagicMock()
        fake_id = ObjectId()
        mock_fs = MagicMock()
        mock_fs.put.return_value = fake_id
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket",
            return_value=mock_fs,
        ):
            result = store_content(db, b"binary", bucket_name="test_bucket")
        assert result == fake_id
        args = mock_fs.put.call_args
        assert args[0][0] == b"binary"


class TestGetContent:
    """Tests for get_content with mocked GridFS."""

    def test_get_returns_decoded_string_when_encoding_utf8(self):
        db = MagicMock()
        oid = ObjectId()
        mock_out = MagicMock()
        mock_out.read.return_value = "hello".encode("utf-8")
        mock_out.metadata = {"encoding": "utf-8"}
        mock_fs = MagicMock()
        mock_fs.get.return_value = mock_out
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket",
            return_value=mock_fs,
        ):
            result = get_content(db, oid, bucket_name="test_bucket")
        assert result == "hello"

    def test_get_returns_bytes_when_no_encoding(self):
        db = MagicMock()
        oid = ObjectId()
        mock_out = MagicMock()
        mock_out.read.return_value = b"raw bytes"
        mock_out.metadata = {}
        mock_fs = MagicMock()
        mock_fs.get.return_value = mock_out
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket",
            return_value=mock_fs,
        ):
            result = get_content(db, oid, bucket_name="test_bucket")
        assert result == b"raw bytes"


class TestDeleteContent:
    """Tests for delete_content with mocked GridFS."""

    def test_delete_no_op_when_database_not_pymongo(self):
        """Covers early return when database is not a real PyMongo Database."""
        oid = ObjectId()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket"
        ) as mock_bucket:
            delete_content(MagicMock(), oid, bucket_name="test_bucket")
        mock_bucket.assert_not_called()

    def test_delete_calls_fs_delete(self):
        db = FakeDatabase()
        oid = ObjectId()
        mock_fs = MagicMock()
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket",
            return_value=mock_fs,
        ):
            delete_content(db, oid, bucket_name="test_bucket")
        mock_fs.delete.assert_called_once_with(oid)

    def test_delete_logs_and_swallows_exception(self):
        """Covers try/except in delete_content when fs.delete raises."""
        db = FakeDatabase()
        oid = ObjectId()
        mock_fs = MagicMock()
        mock_fs.delete.side_effect = Exception("file not found")
        with patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.Database",
            FakeDatabase,
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.get_gridfs_bucket",
            return_value=mock_fs,
        ), patch(
            "mapping_suite_sdk.core.adapters.gridfs_store.logger"
        ) as mock_logger:
            delete_content(db, oid, bucket_name="test_bucket")
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0]
        assert "GridFS delete" in call_args[0]
        assert oid in call_args
        assert "file not found" in str(call_args[-1])
