"""
Service for saving MappingPackageV2 to MongoDB.

This module provides a service to persist MappingPackageV2 models
to a MongoDB database using the MappingPackageV2Saver adapter.
"""
import logging
from typing import Optional

from pymongo import MongoClient

from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_package_saver import MappingPackageV2Saver
# Import from __init__ to ensure id property is patched
from mapping_suite_sdk.mapping_package_v2.models import MappingPackageV2

logger = logging.getLogger(__name__)


@traced_routine
def save_mapping_package_v2_to_mongo_db(
        mapping_package: MappingPackageV2,
        mongo_client: MongoClient,
        database_name: str,
        collection_name: str = "mapping_package",
        package_saver: Optional[MappingPackageV2Saver] = None
) -> MappingPackageV2:
    """Save a MappingPackageV2 model to MongoDB.

    This function simply persists the provided mapping package model to MongoDB
    using the MappingPackageV2Saver adapter. It does not handle extraction or loading.

    Args:
        mapping_package: The MappingPackageV2 model to save.
        mongo_client: MongoDB client instance for database access.
        database_name: Name of the MongoDB database.
        collection_name: Name of the MongoDB collection. Defaults to "mapping_package".
        package_saver: Optional custom saver implementation. If not provided,
            a default MappingPackageV2Saver will be used.

    Returns:
        The saved MappingPackageV2 model.

    Raises:
        ValueError: If MongoDB client is not provided.
        Exception: If database access fails (propagated from repository).
    """
    package_saver = package_saver or MappingPackageV2Saver()

    return package_saver.save(
        mapping_package=mapping_package,
        mongo_client=mongo_client,
        database_name=database_name,
        collection_name=collection_name
    )

