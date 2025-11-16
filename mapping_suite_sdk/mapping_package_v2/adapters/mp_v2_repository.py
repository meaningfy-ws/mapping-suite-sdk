"""
MongoDB repository adapter for MappingPackageV2.

This module provides a MongoDB repository implementation for loading and saving
MappingPackageV2 instances to/from MongoDB collections.
"""

from typing import Any, Dict, List, Optional

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.repository import ModelNotFoundError, RepositoryABC
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2

PACKAGE_VERSION = "v2"
DEFAULT_COLLECTION_NAME = "mapping_packages_v2"


@traced_class
class MappingPackageV2Repository(RepositoryABC[MappingPackageV2]):
    """
    MongoDB repository for MappingPackageV2 instances.

    This repository handles CRUD operations for MappingPackageV2 objects,
    storing them in a dedicated MongoDB collection with version information.
    """

    def __init__(
        self,
        mongo_client: MongoClient,
        database_name: str,
        collection_name: Optional[str] = None
    ):
        """
        Initialize the MappingPackageV2 repository.

        Args:
            mongo_client: MongoDB client instance
            database_name: Name of the MongoDB database
            collection_name: Optional collection name. Defaults to 'mapping_packages_v2'
        """
        self.client = mongo_client
        self.database = self.client[database_name]
        self.collection_name = collection_name or DEFAULT_COLLECTION_NAME
        self.collection = self.database[self.collection_name]

    def create(self, model: MappingPackageV2) -> str:
        """
        Create a new mapping package in MongoDB.

        Args:
            model: The MappingPackageV2 instance to save

        Returns:
            The ID of the created package
        """
        model_dict = model.model_dump(by_alias=True, mode="json")
        model_dict["_id"] = model.id
        model_dict["package_version"] = PACKAGE_VERSION
        self.collection.insert_one(model_dict)
        return model.id

    def read(self, model_id: str) -> MappingPackageV2:
        """
        Read a mapping package from MongoDB by ID.

        Args:
            model_id: The ID of the package to retrieve

        Returns:
            The MappingPackageV2 instance

        Raises:
            ModelNotFoundError: If the package is not found
        """
        result = self.collection.find_one({"_id": model_id})
        if result is None:
            raise ModelNotFoundError(f"Mapping package with ID {model_id} not found")

        # Remove MongoDB-specific fields before validation
        result.pop("_id", None)
        result.pop("package_version", None)

        return MappingPackageV2.model_validate(result)

    def read_many(self, filters: Optional[Dict[str, Any]] = None) -> List[MappingPackageV2]:
        """
        Read multiple mapping packages from MongoDB.

        Args:
            filters: Optional MongoDB query filters

        Returns:
            List of MappingPackageV2 instances
        """
        query = filters or {}
        results = self.collection.find(query)
        models = []
        for doc in results:
            # Remove MongoDB-specific fields before validation
            doc.pop("_id", None)
            doc.pop("package_version", None)
            models.append(MappingPackageV2.model_validate(doc))

        return models

    def update(self, model: MappingPackageV2) -> MappingPackageV2:
        """
        Update an existing mapping package in MongoDB.

        Args:
            model: The MappingPackageV2 instance to update

        Returns:
            The updated MappingPackageV2 instance

        Raises:
            ModelNotFoundError: If the package is not found
        """
        query = {'_id': model.id}
        existing = self.collection.find_one(query)
        if existing is None:
            raise ModelNotFoundError(f"Mapping package with ID {model.id} not found")

        model_dict = model.model_dump(by_alias=True, mode="json")
        model_dict["_id"] = model.id
        model_dict["package_version"] = PACKAGE_VERSION
        self.collection.replace_one(query, model_dict)

        return model

    def delete(self, model_id: str) -> None:
        """
        Delete a mapping package from MongoDB.

        Args:
            model_id: The ID of the package to delete

        Raises:
            ModelNotFoundError: If the package is not found
        """
        result = self.collection.delete_one({'_id': model_id})

        if result.deleted_count < 1:
            raise ModelNotFoundError(f"Mapping package with ID {model_id} not found")

    def __del__(self):
        """Close the MongoDB client connection."""
        self.client.close()

