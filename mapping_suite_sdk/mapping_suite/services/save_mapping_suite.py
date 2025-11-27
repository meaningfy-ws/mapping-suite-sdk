"""
Service for saving mapping suites to MongoDB.

This module provides functionality to persist mapping suite configurations
to a MongoDB database using the MongoDBRepository pattern.
"""
import logging

from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.core.adapters.tracer import traced_routine
# Import from __init__ to ensure id property is patched
from mapping_suite_sdk.mapping_suite.models import MappingSuite

logger = logging.getLogger(__name__)


@traced_routine
def save_mapping_suite_to_mongo_db(
        mapping_suite: MappingSuite,
        mapping_suite_repository: MongoDBRepository[MappingSuite]
) -> MappingSuite:
    """Save a mapping suite to MongoDB.

    This function persists a mapping suite configuration to a MongoDB database
    using the provided repository. The suite is stored with its identifier
    (from mapping_suite_config.mapping_suite_metadata.mapping_suite_identifier)
    as the document _id.

    Args:
        mapping_suite (MappingSuite): The mapping suite to save to MongoDB.
        mapping_suite_repository (MongoDBRepository[MappingSuite]): Repository instance
            for accessing MongoDB.

    Returns:
        MappingSuite: The saved mapping suite.

    Raises:
        ValueError: If mapping suite or repository is missing/None.
        Exception: If database access fails (propagated from repository).
    """
    if not mapping_suite:
        raise ValueError("Mapping suite must be provided")

    if not mapping_suite_repository:
        raise ValueError("MongoDB repository must be provided")

    return mapping_suite_repository.create(mapping_suite)

