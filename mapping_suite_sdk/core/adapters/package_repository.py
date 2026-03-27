"""
Repository implementation specifically for mapping packages.

This module provides PackageRepository, which extends MongoDBRepository
with package-specific convenience methods and intercepts CRUD to store/retrieve
large file content in GridFS so the main document stays under MongoDB's 16MB limit.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.gridfs_store import (
    DEFAULT_GRIDFS_THRESHOLD_BYTES,
    collect_gridfs_ids_from_doc,
    delete_content,
    prepare_doc_for_insert,
    resolve_doc_gridfs_refs,
)
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository, ModelNotFoundError
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.models.pydantic import PydanticModel

T = TypeVar("T", bound=PydanticModel)


@traced_class
class PackageRepository(MongoDBRepository[T]):
    """Repository implementation for mapping packages.

    Extends MongoDBRepository with package-specific methods and intercepts
    create/read/update/delete: any document field named 'content' (file assets)
    at or above the configured size threshold is stored in GridFS; the document
    holds only a reference. On read, references are resolved so the caller
    receives the full model. Callers use the same repository for save and load.
    """

    def __init__(
        self,
        model_class: Type[T],
        mongo_client: MongoClient,
        database_name: str,
        collection_name: str = "mapping_package",
        gridfs_threshold_bytes: int = DEFAULT_GRIDFS_THRESHOLD_BYTES,
        gridfs_bucket_name: str = "gridfs_package_assets",
    ):
        """Initialize a PackageRepository.

        Args:
            model_class: The Pydantic model class for the mapping package.
            mongo_client: MongoDB client instance.
            database_name: Name of the MongoDB database.
            collection_name: Name of the MongoDB collection. Defaults to "mapping_package".
            gridfs_threshold_bytes: Size above which 'content' fields are stored in GridFS.
            gridfs_bucket_name: GridFS bucket/collection prefix for large content.
        """
        super().__init__(
            model_class=model_class,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name,
        )
        self._gridfs_threshold = gridfs_threshold_bytes
        self._gridfs_bucket = gridfs_bucket_name

    def create(self, model: T) -> T:
        model_id = model.id
        model_dict = model.model_dump(by_alias=True, mode="json")
        model_dict["_id"] = model_id
        prepare_doc_for_insert(
            model_dict,
            self.database,
            threshold_bytes=self._gridfs_threshold,
            bucket_name=self._gridfs_bucket,
        )
        self.collection.insert_one(model_dict)
        return model

    def read(self, model_id: str) -> T:
        result = self.collection.find_one({"_id": model_id})
        if result is None:
            raise ModelNotFoundError(f"Asset with ID {model_id} not found")
        result_dict = dict(result)
        resolve_doc_gridfs_refs(result_dict, self.database, bucket_name=self._gridfs_bucket)
        if "_id" in result_dict:
            model_fields = self.model_class.model_fields
            if "id" in model_fields or any(
                field.alias == "_id" for field in model_fields.values()
            ):
                result_dict["id"] = result_dict.pop("_id")
            else:
                result_dict.pop("_id")
        return self.model_class.model_validate(result_dict)

    def read_many(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        query = filters or {}
        results = self.collection.find(query)
        models = []
        model_fields = self.model_class.model_fields
        has_id_field = "id" in model_fields or any(
            field.alias == "_id" for field in model_fields.values()
        )
        for doc in results:
            doc_dict = dict(doc)
            resolve_doc_gridfs_refs(doc_dict, self.database, bucket_name=self._gridfs_bucket)
            if "_id" in doc_dict:
                if has_id_field:
                    doc_dict["id"] = doc_dict.pop("_id")
                else:
                    doc_dict.pop("_id")
            models.append(self.model_class.model_validate(doc_dict))
        return models

    def update(self, model: T) -> T:
        query = {"_id": model.id}
        existing = self.collection.find_one(query)
        if existing is None:
            raise ModelNotFoundError(f"Asset with ID {model.id} not found")
        old_gridfs_ids = collect_gridfs_ids_from_doc(existing)
        model_id = model.id
        model_dict = model.model_dump(by_alias=True, mode="json")
        model_dict["_id"] = model_id
        prepare_doc_for_insert(
            model_dict,
            self.database,
            threshold_bytes=self._gridfs_threshold,
            bucket_name=self._gridfs_bucket,
        )
        self.collection.replace_one(query, model_dict)
        for oid in old_gridfs_ids:
            delete_content(self.database, oid, bucket_name=self._gridfs_bucket)
        return model

    def delete(self, model_id: str) -> None:
        doc = self.collection.find_one({"_id": model_id})
        if doc is None:
            raise ModelNotFoundError(f"Asset with ID {model_id} not found")
        gridfs_ids = collect_gridfs_ids_from_doc(doc)
        self.collection.delete_one({"_id": model_id})
        for oid in gridfs_ids:
            delete_content(self.database, oid, bucket_name=self._gridfs_bucket)
        return None

    def create_package(self, model: T) -> T:
        """Create a mapping package in MongoDB.

        This is a convenience method that wraps create() for better domain clarity
        when working with mapping packages.

        Args:
            model: The mapping package model to save.

        Returns:
            The saved mapping package model.
        """
        return self.create(model)

