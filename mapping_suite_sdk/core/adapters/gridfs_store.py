"""
GridFS storage for large file content in mapping packages.

This module provides helpers to store and retrieve large string/binary content
in MongoDB GridFS so that the main package document stays under the 16MB BSON limit.

Content is stored inline on the document when below a size threshold; above the
threshold it is moved into GridFS and the document holds a reference via
:data:`GRIDFS_REF_KEY`. The threshold is controlled by :data:`DEFAULT_GRIDFS_THRESHOLD_BYTES`
(1 MiB) or a caller-supplied ``threshold_bytes`` in the higher-level serialization
helpers (:func:`prepare_doc_for_insert`, etc.). The low-level helpers here
(:func:`store_content`, :func:`get_content`, :func:`delete_content`) operate
directly on GridFS.
"""
import logging
from typing import Any, Dict, List, MutableMapping, Optional, Union

from bson import ObjectId
from gridfs import GridFS
from gridfs.errors import NoFile
from pymongo.database import Database

logger = logging.getLogger(__name__)

# Key used in document to mark content stored in GridFS
GRIDFS_REF_KEY = "_gridfs_id"
# Document key for fields eligible for GridFS storage when above size threshold
GRIDFS_CONTENT_FIELD_NAME = "content"
# Metadata key for encoding when content was stored as string (utf-8)
GRIDFS_METADATA_ENCODING = "encoding"

# Default size threshold above which content is stored in GridFS (1 MiB)
DEFAULT_GRIDFS_THRESHOLD_BYTES = 1024 * 1024


def get_gridfs_bucket(database: Database, bucket_name: str = "gridfs_package_assets") -> GridFS:
    """Return a GridFS instance for the given database and bucket name."""
    return GridFS(database, collection=bucket_name)


def store_content(
    database: Database,
    content: str | bytes,
    metadata: Optional[Dict[str, Any]] = None,
    bucket_name: str = "gridfs_package_assets",
) -> ObjectId:
    """Store content in GridFS and return the file ID.

    Args:
        database: MongoDB database.
        content: String or bytes to store. Strings are stored as UTF-8 bytes.
        metadata: Optional metadata dict (e.g. {"encoding": "utf-8"} for str).
        bucket_name: GridFS bucket/collection prefix.

    Returns:
        ObjectId of the stored file.
    """
    fs = get_gridfs_bucket(database, bucket_name=bucket_name)
    meta = dict(metadata or {})
    if isinstance(content, str):
        data = content.encode("utf-8")
        meta[GRIDFS_METADATA_ENCODING] = "utf-8"
    else:
        data = content
    file_id = fs.put(data, metadata=meta)
    return file_id


def get_content(
    database: Database,
    file_id: ObjectId,
    bucket_name: str = "gridfs_package_assets",
) -> str | bytes:
    """Retrieve content from GridFS by file ID.

    Args:
        database: MongoDB database.
        file_id: GridFS file ObjectId.
        bucket_name: GridFS bucket/collection prefix.

    Returns:
        Decoded string if metadata has encoding, otherwise bytes.
    """
    fs = get_gridfs_bucket(database, bucket_name=bucket_name)
    grid_out = fs.get(file_id)
    data = grid_out.read()
    meta = grid_out.metadata or {}
    if meta.get(GRIDFS_METADATA_ENCODING) == "utf-8":
        return data.decode("utf-8")
    return data


def delete_content(
    database: Union[Database, Any],
    file_id: ObjectId,
    bucket_name: str = "gridfs_package_assets",
) -> None:
    """Delete a file from GridFS by ID.

    No-op if database is not a real PyMongo Database (e.g. mongomock).
    If the file does not exist (NoFile), logs at debug; other errors are
    logged at warning and re-raised so callers can handle them.

    Args:
        database: Real PyMongo Database or mock (e.g. mongomock); Union is used
            so callers can pass in-memory DBs; non-Database results in an immediate no-op.
        file_id: GridFS file ObjectId.
        bucket_name: GridFS bucket/collection prefix.
    """
    if not isinstance(database, Database):
        return
    fs = get_gridfs_bucket(database, bucket_name=bucket_name)
    try:
        fs.delete(file_id)
    except NoFile:
        logger.debug("GridFS delete %s: file not found (no-op)", file_id)
    except Exception as e:
        logger.warning("GridFS delete %s: %s", file_id, e)
        raise


def _collect_gridfs_ids(obj: Any, out: List[ObjectId]) -> None:
    """Recursively collect all _gridfs_id values from a document."""
    if isinstance(obj, dict):
        if GRIDFS_REF_KEY in obj and isinstance(obj[GRIDFS_REF_KEY], ObjectId):
            out.append(obj[GRIDFS_REF_KEY])
        for v in obj.values():
            _collect_gridfs_ids(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_gridfs_ids(item, out)


def _serialize_content_to_gridfs(
    obj: Any,
    database: Database,
    threshold_bytes: int,
    bucket_name: str,
) -> None:
    """Recursively replace large 'content' values with GridFS references (mutates obj)."""
    if isinstance(obj, MutableMapping):
        for key, value in list(obj.items()):
            if key == GRIDFS_CONTENT_FIELD_NAME and isinstance(value, (str, bytes)):
                size = len(value) if isinstance(value, bytes) else len(value.encode("utf-8"))
                if size >= threshold_bytes:
                    file_id = store_content(
                        database,
                        value,
                        metadata={},
                        bucket_name=bucket_name,
                    )
                    obj[key] = {GRIDFS_REF_KEY: file_id}
                else:
                    # leave as-is
                    pass
            else:
                _serialize_content_to_gridfs(value, database, threshold_bytes, bucket_name)
    elif isinstance(obj, list):
        for item in obj:
            _serialize_content_to_gridfs(item, database, threshold_bytes, bucket_name)


def _resolve_gridfs_refs(
    obj: Any,
    database: Database,
    bucket_name: str,
) -> None:
    """Recursively replace GridFS reference dicts with actual content (mutates obj)."""
    if isinstance(obj, MutableMapping):
        for key, value in list(obj.items()):
            if (
                key == GRIDFS_CONTENT_FIELD_NAME
                and isinstance(value, dict)
                and GRIDFS_REF_KEY in value
                and isinstance(value[GRIDFS_REF_KEY], ObjectId)
            ):
                obj[key] = get_content(
                    database,
                    value[GRIDFS_REF_KEY],
                    bucket_name=bucket_name,
                )
            else:
                _resolve_gridfs_refs(value, database, bucket_name)
    elif isinstance(obj, list):
        for item in obj:
            _resolve_gridfs_refs(item, database, bucket_name)


def prepare_doc_for_insert(
    doc: MutableMapping[str, Any],
    database: Union[Database, Any],
    threshold_bytes: int = DEFAULT_GRIDFS_THRESHOLD_BYTES,
    bucket_name: str = "gridfs_package_assets",
) -> None:
    """Mutate the document in place: replace large 'content' fields with GridFS references.

    If database is not a real pymongo Database (e.g. mongomock), no replacement
    is done so existing tests that use in-memory DBs continue to work.

    Args:
        doc: Document to mutate (nested 'content' fields may be replaced with refs).
        database: Real PyMongo Database or mock (e.g. mongomock); Union is used
            so callers can pass in-memory DBs; non-Database results in an immediate no-op.
        threshold_bytes: Minimum size in bytes for moving content to GridFS.
        bucket_name: GridFS bucket/collection prefix.
    """
    if not isinstance(database, Database):
        return
    _serialize_content_to_gridfs(doc, database, threshold_bytes, bucket_name)


def resolve_doc_gridfs_refs(
    doc: MutableMapping[str, Any],
    database: Union[Database, Any],
    bucket_name: str = "gridfs_package_assets",
) -> None:
    """Mutate the document in place: replace GridFS reference objects with actual content.

    If database is not a real pymongo Database, refs are left as-is (caller may
    have stored with inline content when using e.g. mongomock).

    Args:
        doc: Document to mutate (GridFS refs will be replaced with content).
        database: Real PyMongo Database or mock (e.g. mongomock); Union is used
            so callers can pass in-memory DBs; non-Database results in an immediate no-op.
        bucket_name: GridFS bucket/collection prefix.
    """
    if not isinstance(database, Database):
        return
    _resolve_gridfs_refs(doc, database, bucket_name)


def collect_gridfs_ids_from_doc(doc: Any) -> List[ObjectId]:
    """Collect all GridFS file IDs referenced in a document."""
    out: List[ObjectId] = []
    _collect_gridfs_ids(doc, out)
    return out
