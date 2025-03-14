from pathlib import Path
from typing import Optional, Literal, NoReturn

from mapping_suite_sdk.adapters.tracer import traced_routine
from mapping_suite_sdk.adapters.validator import MappingPackageValidator
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.services.load_mapping_package import load_mapping_package_from_archive


@traced_routine
def validate_mapping_package(
        mapping_package: MappingPackage,
        mp_validator: Optional[MappingPackageValidator] = None) -> Literal[True] | NoReturn:
    if not mp_validator:
        mp_validator = MappingPackageValidator()

    return mp_validator.validate(mapping_package=mapping_package)


@traced_routine
def validate_mapping_package_from_archive(
        mapping_package_archive_path: Path,
        mp_validator: Optional[MappingPackageValidator] = None) -> Literal[True] | NoReturn:
    if not mp_validator:
        mp_validator = MappingPackageValidator()

    mapping_package: MappingPackage = load_mapping_package_from_archive(mapping_package_archive_path)

    return mp_validator.validate(mapping_package=mapping_package)
