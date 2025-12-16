"""
Service for saving MappingPackageV3Lightweight to MongoDB.

This module provides a service to persist MappingPackageV3Lightweight models
to a MongoDB database using the MappingPackageV3LightweightSaver adapter.
"""
import logging
from typing import Optional

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_saver import MappingPackageV3LightweightSaver
# Import from __init__ to ensure id property is patched
from mapping_suite_sdk.mapping_package_v3.models import MappingPackageV3Lightweight

logger = logging.getLogger(__name__)


@traced_routine
def save_mapping_package_v3_lightweight_to_mongo_db(
        mapping_package: MappingPackageV3Lightweight,
        mongo_client: MongoClient,
        database_name: str,
        collection_name: str = "mapping_package",
        package_saver: Optional[MappingPackageV3LightweightSaver] = None
) -> MappingPackageV3Lightweight:
    """Save a MappingPackageV3Lightweight model to MongoDB.

    This function simply persists the provided mapping package model to MongoDB
    using the MappingPackageV3LightweightSaver adapter. It does not handle extraction or loading.

    Args:
        mapping_package: The MappingPackageV3Lightweight model to save.
        mongo_client: MongoDB client instance for database access.
        database_name: Name of the MongoDB database.
        collection_name: Name of the MongoDB collection. Defaults to "mapping_package".
        package_saver: Optional custom saver implementation. If not provided,
            a default MappingPackageV3LightweightSaver will be used.

    Returns:
        The saved MappingPackageV3Lightweight model.

    Raises:
        ValueError: If MongoDB client is not provided.
        Exception: If database access fails (propagated from repository).
    """
    package_saver = package_saver or MappingPackageV3LightweightSaver()

    return package_saver.save(
        mapping_package=mapping_package,
        mongo_client=mongo_client,
        database_name=database_name,
        collection_name=collection_name
    )

