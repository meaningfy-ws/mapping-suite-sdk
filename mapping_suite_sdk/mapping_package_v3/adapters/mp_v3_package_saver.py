"""
Adapter for saving MappingPackageV3 to MongoDB.

This adapter saves v3 mapping package models to MongoDB.
"""
import logging

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.gridfs_repository import GridFSPackageRepository
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3

logger = logging.getLogger(__name__)


@traced_class
class MappingPackageV3Saver:
    """Saver for MappingPackageV3 to MongoDB."""

    def save(
            self,
            mapping_package: MappingPackageV3,
            mongo_client: MongoClient,
            database_name: str,
            collection_name: str = "mapping_package"
    ) -> MappingPackageV3:
        """Save a v3 mapping package model to MongoDB.

        Args:
            mapping_package: The mapping package model to save.
            mongo_client: MongoDB client instance.
            database_name: Name of the MongoDB database.
            collection_name: Name of the MongoDB collection. Defaults to "mapping_package".

        Returns:
            The saved mapping package model.
        """
        if not mongo_client:
            raise ValueError("MongoDB client must be provided")

        repository = GridFSPackageRepository[MappingPackageV3](
            model_class=MappingPackageV3,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

        return repository.create_package(mapping_package)

