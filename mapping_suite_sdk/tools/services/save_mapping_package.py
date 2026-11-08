"""Version-agnostic save of a loaded mapping package to MongoDB (needs the [mongodb] extra)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mapping_suite_sdk.core.adapters.optional_dependency import require
from mapping_suite_sdk.core.adapters.package_repository import PackageRepository
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.tools.services.convert_mapping_package import UnsupportedConversionError

if TYPE_CHECKING:
    from pymongo import MongoClient


@traced_routine
def save_mapping_package_to_mongodb(
    mapping_package: MappingPackageV3 | MappingPackageV3Lightweight,
    mongo_client: MongoClient,
    database_name: str,
    collection_name: str = "mapping_package",
) -> MappingPackageV3 | MappingPackageV3Lightweight:
    """Save a v3 or v3-lightweight package, as returned by ``load_mapping_package``, to MongoDB.

    The package is upserted by its id, so saving it again updates the stored document.

    Raises:
        ImportError: If the [mongodb] extra is not installed.
        UnsupportedConversionError: If the package is neither v3 nor v3-lightweight.
    """
    require("pymongo", "mongodb", "MongoDB")
    if not isinstance(mapping_package, (MappingPackageV3, MappingPackageV3Lightweight)):
        raise UnsupportedConversionError(f"Cannot persist to MongoDB: unsupported package type {type(mapping_package)}")
    repository = PackageRepository(type(mapping_package), mongo_client, database_name, collection_name)
    return repository.upsert(mapping_package)
