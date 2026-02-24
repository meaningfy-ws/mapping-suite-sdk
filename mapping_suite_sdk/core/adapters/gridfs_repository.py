"""
Deprecated: GridFS interception is now in PackageRepository.

GridFSPackageRepository is retained as an alias for backward compatibility.
Callers should use PackageRepository; it intercepts CRUD and uses GridFS for large content.
"""
import warnings
from typing import Type, TypeVar

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.gridfs_store import DEFAULT_GRIDFS_THRESHOLD_BYTES
from mapping_suite_sdk.core.adapters.package_repository import PackageRepository
from mapping_suite_sdk.core.models.pydantic import PydanticModel

T = TypeVar("T", bound=PydanticModel)


class GridFSPackageRepository(PackageRepository[T]):
    """Deprecated: Use PackageRepository. It now performs GridFS interception internally."""

    def __init__(
        self,
        model_class: Type[T],
        mongo_client: MongoClient,
        database_name: str,
        collection_name: str = "mapping_package",
        gridfs_threshold_bytes: int = DEFAULT_GRIDFS_THRESHOLD_BYTES,
        gridfs_bucket_name: str = "gridfs_package_assets",
    ):
        warnings.warn(
            "GridFSPackageRepository is deprecated; use PackageRepository. "
            "PackageRepository intercepts CRUD and uses GridFS for large content.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            model_class=model_class,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name,
            gridfs_threshold_bytes=gridfs_threshold_bytes,
            gridfs_bucket_name=gridfs_bucket_name,
        )
