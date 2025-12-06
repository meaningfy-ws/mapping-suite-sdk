"""
Service for saving mapping packages to MongoDB.

This module provides a simple service to persist mapping package models
to a MongoDB database using the PackageRepository pattern.
"""
import logging
from typing import Union

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.package_repository import PackageRepository
from mapping_suite_sdk.core.adapters.tracer import traced_routine
# Import from __init__ to ensure id property is patched
from mapping_suite_sdk.mapping_package_v1.models import MappingPackageV1
from mapping_suite_sdk.mapping_package_v2.models import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models import MappingPackageV3, MappingPackageV3Lightweight

logger = logging.getLogger(__name__)


@traced_routine
def save_mapping_package_to_mongo_db(
        mapping_package: Union[MappingPackageV1, MappingPackageV2, MappingPackageV3, MappingPackageV3Lightweight],
        mongo_client: MongoClient,
        database_name: str,
        collection_name: str = "mapping_package"
) -> Union[MappingPackageV1, MappingPackageV2, MappingPackageV3, MappingPackageV3Lightweight]:
    """Save a mapping package model to MongoDB.

    This function simply persists the provided mapping package model to MongoDB
    using the PackageRepository. It does not handle extraction or loading.

    Args:
        mapping_package: The mapping package model to save.
        mongo_client: MongoDB client instance for database access.
        database_name: Name of the MongoDB database.
        collection_name: Name of the MongoDB collection. Defaults to "mapping_package".

    Returns:
        The saved mapping package model.

    Raises:
        ValueError: If MongoDB client is not provided.
        Exception: If database access fails (propagated from repository).
    """
    if not mongo_client:
        raise ValueError("MongoDB client must be provided")

    # Determine the model class and create appropriate repository
    if isinstance(mapping_package, MappingPackageV1):
        repository = PackageRepository[MappingPackageV1](
            model_class=MappingPackageV1,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
    elif isinstance(mapping_package, MappingPackageV2):
        repository = PackageRepository[MappingPackageV2](
            model_class=MappingPackageV2,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
    elif isinstance(mapping_package, MappingPackageV3):
        repository = PackageRepository[MappingPackageV3](
            model_class=MappingPackageV3,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
    elif isinstance(mapping_package, MappingPackageV3Lightweight):
        repository = PackageRepository[MappingPackageV3Lightweight](
            model_class=MappingPackageV3Lightweight,
            mongo_client=mongo_client,
            database_name=database_name,
            collection_name=collection_name
        )
    else:
        raise ValueError(f"Unsupported mapping package type: {type(mapping_package)}")

    return repository.create_package(mapping_package)

