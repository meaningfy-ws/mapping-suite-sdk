"""
Repository implementation specifically for mapping packages.

This module provides PackageRepository, which extends MongoDBRepository
with package-specific convenience methods.
"""
from typing import Type, TypeVar

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.models.pydantic import PydanticModel

T = TypeVar('T', bound=PydanticModel)


@traced_class
class PackageRepository(MongoDBRepository[T]):
    """Repository implementation for mapping packages.

    This class extends MongoDBRepository with package-specific methods
    for better domain clarity when working with mapping packages.
    """

    def __init__(
            self,
            model_class: Type[T],
            mongo_client: MongoClient,
            database_name: str,
            collection_name: str = "mapping_package"
    ):
        """Initialize a PackageRepository.

        Args:
            model_class: The Pydantic model class for the mapping package.
            mongo_client: MongoDB client instance.
            database_name: Name of the MongoDB database.
            collection_name: Name of the MongoDB collection. Defaults to "mapping_package".
        """
        super().__init__(
            model_class=model_class,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )

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

