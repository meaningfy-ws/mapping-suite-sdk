import json
import logging
from pathlib import Path
from typing import Optional, Literal, NoReturn, List

from pydantic import ValidationError

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor, GitHubExtractor
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.core.adapters.validator_abc import MPValidationException
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import MappingPackageV3LightweightLoader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import \
    load_mapping_package_v3_from_archive, \
    load_mapping_package_v3_from_folder, \
    load_mapping_packages_v3_from_github

logger = logging.getLogger(__name__)


@traced_routine
def validate_mapping_package_v3_lightweight(
        mapping_package: MappingPackageV3Lightweight) -> Literal[True] | NoReturn:
    """
    Validates the given Mapping Package V3 Lightweight by checking the hash.

    Args:
        mapping_package (MappingPackageV3Lightweight): The Mapping Package instance to validate.

    Returns:
        Literal[True] | NoReturn: True if the validation passes, otherwise raises an exception.
    """
    hasher = MappingPackageV3Hasher(mapping_package)  # type: ignore[arg-type]
    expected_hash = hasher.hash()
    actual_hash = mapping_package.metadata.mapping_suite_hash_digest

    if actual_hash and expected_hash != actual_hash:
        raise MPValidationException(f"Hash validation failed. Expected: {expected_hash}, Got: {actual_hash}")

    return True


@traced_routine
def validate_mapping_package_v3_lightweight_from_archive(
        mapping_package_archive_path: Path,
        mapping_package_loader: Optional[MappingPackageV3LightweightLoader] = None,
        archive_unpacker: Optional[ArchiveExtractor] = None
) -> Literal[True] | NoReturn:
    from mapping_suite_sdk.core.adapters.validator_abc import MPValidationStepABC

    MPValidationStepABC.validate_archive_path(
        path=mapping_package_archive_path,
        context="validate package from archive"
    )

    mapping_package: MappingPackageV3Lightweight = load_mapping_package_v3_from_archive(
        mapping_package_archive_path=mapping_package_archive_path,
        mapping_package_loader=mapping_package_loader,
        archive_unpacker=archive_unpacker)

    return validate_mapping_package_v3_lightweight(mapping_package=mapping_package)


@traced_routine
def validate_mapping_package_v3_lightweight_from_folder(
        mapping_package_folder_path: Path,
        mapping_package_loader: Optional[MappingPackageV3LightweightLoader] = None) -> Literal[True] | NoReturn:
    from mapping_suite_sdk.core.adapters.validator_abc import MPValidationStepABC

    MPValidationStepABC.validate_folder_path(
        path=mapping_package_folder_path,
        context="validate package from folder"
    )

    mapping_package: MappingPackageV3Lightweight = load_mapping_package_v3_from_folder(
        mapping_package_folder_path=mapping_package_folder_path,
        mapping_package_loader=mapping_package_loader,
    )

    return validate_mapping_package_v3_lightweight(mapping_package=mapping_package)


@traced_routine
def validate_bulk_mapping_packages_v3_lightweight_from_folder(
        mapping_packages_folder_path: Path,
        mapping_package_loader: Optional[MappingPackageV3LightweightLoader] = None,
        update_hash: bool = False,
) -> bool | NoReturn:
    from mapping_suite_sdk.core.adapters.validator_abc import MPValidationStepABC

    MPValidationStepABC.validate_folder_path(
        path=mapping_packages_folder_path,
        context="bulk validate packages from folder"
    )

    all_valid: bool = True
    for mp_folder in mapping_packages_folder_path.iterdir():
        try:
            if not mp_folder.is_dir():
                continue

            validate_mapping_package_v3_lightweight_from_folder(mapping_package_folder_path=mp_folder,
                                                                mapping_package_loader=mapping_package_loader)
        except MPValidationException as hash_validation_exception:
            message: str = f"Mapping package is not valid: {hash_validation_exception}"
            if update_hash:
                message += f"\n🔀  The hash for {mp_folder} is changed."
                metadata_file = Path(mp_folder / "metadata.jsonld")
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    lightweight_package = load_mapping_package_v3_from_folder(mp_folder)
                    metadata['mapping_suite_hash_digest'] = MappingPackageV3Hasher(lightweight_package).hash()  # type: ignore[arg-type]
                    metadata_file.write_text(json.dumps(metadata, indent=4))
            else:
                all_valid = False
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mp_folder,
                                                                          message=message))
            continue
        except (ValidationError) as validation_exception:
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mp_folder,
                                                                          message=f"Mapping package is not valid: {validation_exception}"))
            all_valid = False
            continue
        except Exception as other_exception:
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mp_folder,
                                                                          message=f"Cannot validate mapping package: {other_exception}\n skipping"))
            all_valid = False
            continue
        else:
            logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mp_folder,
                                                                         message="Mapping package is valid ✅"))
    return all_valid


@traced_routine
def validate_bulk_mapping_packages_v3_lightweight_from_github(
        github_repository_url: str,
        packages_path_pattern: str,
        branch_or_tag_name: Optional[str] = None,
        github_package_extractor: Optional[GitHubExtractor] = None,
        mapping_package_loader: Optional[MappingPackageV3LightweightLoader] = None,
) -> bool | NoReturn:
    from mapping_suite_sdk.core.adapters.validator_abc import MPValidationStepABC

    MPValidationStepABC.validate_string_parameter(
        value=github_repository_url,
        param_name="Repository URL",
        context="validate packages from github"
    )

    MPValidationStepABC.validate_string_parameter(
        value=packages_path_pattern,
        param_name="Packages path pattern",
        context="validate packages from github"
    )

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=f"URL: {github_repository_url} | branch_or_tag_name: {branch_or_tag_name} | pattern: {packages_path_pattern}",
        message="Validating bulk mapping packages from Github"))

    mapping_packages: List[MappingPackageV3Lightweight] = load_mapping_packages_v3_from_github(
        github_repository_url=github_repository_url,
        packages_path_pattern=packages_path_pattern,
        branch_or_tag_name=branch_or_tag_name,
        github_package_extractor=github_package_extractor,
        mapping_package_loader=mapping_package_loader)

    all_valid: bool = True
    for mapping_package in mapping_packages:
        try:
            validate_mapping_package_v3_lightweight(mapping_package=mapping_package)
        except MPValidationException as validation_exception:
            logger.error(
                mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package.metadata.id,
                                                                 message=f"Mapping package is not valid: {validation_exception}"))
            all_valid = False
            continue
        except Exception as unexpected_exception:
            logger.error(
                mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package.metadata.id,
                                                                 message=f"Unexpected exception raised: {unexpected_exception}"))
            all_valid = False
            continue
        else:
            logger.info(
                mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package.metadata.id,
                                                                 message="✅ The package is valid!"))
    return all_valid


