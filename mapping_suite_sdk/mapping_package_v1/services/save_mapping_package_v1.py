"""
Service for saving MappingPackageV1 to MongoDB.

This module provides a service to persist MappingPackageV1 models
to a MongoDB database using the MappingPackageV1Saver adapter.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mapping_suite_sdk.core.adapters.optional_dependency import require
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_package_saver import MappingPackageV1Saver

# Import from __init__ to ensure id property is patched
from mapping_suite_sdk.mapping_package_v1.models import MappingPackageV1

if TYPE_CHECKING:
    from pymongo import MongoClient

logger = logging.getLogger(__name__)


@traced_routine
def save_mapping_package_v1_to_mongo_db(
    mapping_package: MappingPackageV1,
    mongo_client: MongoClient,
    database_name: str,
    collection_name: str = "mapping_package",
    package_saver: MappingPackageV1Saver | None = None,
) -> MappingPackageV1:
    """Save a MappingPackageV1 model to MongoDB.

    This function simply persists the provided mapping package model to MongoDB
    using the MappingPackageV1Saver adapter. It does not handle extraction or loading.

    Args:
        mapping_package: The MappingPackageV1 model to save.
        mongo_client: MongoDB client instance for database access.
        database_name: Name of the MongoDB database.
        collection_name: Name of the MongoDB collection. Defaults to "mapping_package".
        package_saver: Optional custom saver implementation. If not provided,
            a default MappingPackageV1Saver will be used.

    Returns:
        The saved MappingPackageV1 model.

    Raises:
        ValueError: If MongoDB client is not provided.
        Exception: If database access fails (propagated from repository).
    """
    require("pymongo", "mongodb", "MongoDB")
    package_saver = package_saver or MappingPackageV1Saver()

    return package_saver.save(
        mapping_package=mapping_package,
        mongo_client=mongo_client,
        database_name=database_name,
        collection_name=collection_name,
    )
