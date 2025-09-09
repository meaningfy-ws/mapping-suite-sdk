import json
import logging
from pathlib import Path
from typing import Optional, Literal, NoReturn, List

from pydantic import ValidationError

from mapping_suite_sdk import ArchivePackageExtractor, GithubPackageExtractor, MappingPackageHasher
from mapping_suite_sdk.adapters.loader import MappingPackageAssetLoader
from mapping_suite_sdk.adapters.tracer import traced_routine
from mapping_suite_sdk.adapters.validator import MappingPackageValidator, MPValidationException, \
    MPHashValidationException
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.services.load_mapping_package import load_mapping_package_from_archive, \
    load_mapping_package_from_folder, load_mapping_packages_from_github
from mapping_suite_sdk.vars import MSSDK_LOGGING_MESSAGE_FORMAT

logger = logging.getLogger(__name__)


@traced_routine
def validate_mapping_package(
        mapping_package: MappingPackage,
        mp_validator: Optional[MappingPackageValidator] = None) -> Literal[True] | NoReturn:
    """
    Validates the given Mapping Package using the provided MappingPackageValidator.

    Args:
        mapping_package (MappingPackage): The Mapping Package instance to validate.
        mp_validator (Optional[MappingPackageValidator]): The MappingPackageValidator to use for validation. If not provided, a new instance will be created.

    Returns:
        Literal[True] | NoReturn: True if the validation passes, otherwise raises an exception.
    """
    if not mp_validator:
        mp_validator = MappingPackageValidator()

    return mp_validator.validate(mapping_package=mapping_package)


@traced_routine
def validate_mapping_package_from_archive(
        mapping_package_archive_path: Path,
        mp_validator: Optional[MappingPackageValidator] = None,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None,
        archive_unpacker: Optional[ArchivePackageExtractor] = None
) -> Literal[True] | NoReturn:
    if not mapping_package_archive_path.exists():
        message: str = f"Cannot validate package from archive. Archive path does not exist: {mapping_package_archive_path}"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package_archive_path,
                                                         message=message))
        raise FileNotFoundError(message)

    if not mapping_package_archive_path.is_file():
        message: str = f"Cannot validate package from archive. Path is not a file: {mapping_package_archive_path}"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package_archive_path,
                                                         message=message))
        raise FileNotFoundError(message)

    mapping_package: MappingPackage = load_mapping_package_from_archive(
        mapping_package_archive_path=mapping_package_archive_path,
        mapping_package_loader=mapping_package_loader,
        archive_unpacker=archive_unpacker)

    return validate_mapping_package(mapping_package=mapping_package, mp_validator=mp_validator)


@traced_routine
def validate_mapping_package_from_folder(
        mapping_package_folder_path: Path,
        mp_validator: Optional[MappingPackageValidator] = None,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None) -> Literal[True] | NoReturn:
    if not mapping_package_folder_path.exists():
        message: str = f"Cannot validate package from folder. Folder path does not exist: {mapping_package_folder_path}"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package_folder_path,
                                                         message=message))
        raise FileNotFoundError(message)

    if not mapping_package_folder_path.is_dir():
        message: str = f"Cannot validate package from folder. Path is not a directory: {mapping_package_folder_path}"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package_folder_path,
                                                         message=message))
        raise NotADirectoryError(message)

    mapping_package: MappingPackage = load_mapping_package_from_folder(
        mapping_package_folder_path=mapping_package_folder_path,
        mapping_package_loader=mapping_package_loader,
    )

    return validate_mapping_package(mapping_package=mapping_package, mp_validator=mp_validator)


@traced_routine
def validate_bulk_mapping_packages_from_folder(
        mapping_packages_folder_path: Path,
        mp_validator: Optional[MappingPackageValidator] = None,
        mapping_package_loader: Optional[MappingPackageAssetLoader] = None,
        update_hash: bool = False,
) -> bool | NoReturn:
    if not mapping_packages_folder_path.exists():
        message: str = f"Cannot bulk validate packages form folder. Folder path does not exist: {mapping_packages_folder_path}"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_packages_folder_path,
                                                         message=message))
        raise FileNotFoundError(message)

    if not mapping_packages_folder_path.is_dir():
        message: str = f"Cannot bulk validate packages from folder. Cannot validate package. Path is not a directory: {mapping_packages_folder_path}"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_packages_folder_path,
                                                         message=message))
        raise NotADirectoryError(message)

    all_valid: bool = True
    for mp_folder in mapping_packages_folder_path.iterdir():
        try:
            validate_mapping_package_from_folder(mapping_package_folder_path=mp_folder,
                                                 mp_validator=mp_validator,
                                                 mapping_package_loader=mapping_package_loader,)
        except MPHashValidationException as hash_validation_exception:
            # TODO: Temporary solution. This logic needs to be in the validator.
            #  It will be done there when MSSDK will have Full MP support (currently no support for output folder)
            message: str = f"Mapping package is not valid: {hash_validation_exception}"
            if update_hash:
                message += f"\n🔀  The hash for {mp_folder} is changed."
                metadata_file = Path(mp_folder / "metadata.json")
                metadata = json.loads(metadata_file.read_text())
                metadata['mapping_suite_hash_digest'] = MappingPackageHasher(
                    load_mapping_package_from_folder(mp_folder)).hash_mapping_package()
                metadata_file.write_text(json.dumps(metadata, indent=4))
            else:
                all_valid = False
            logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mp_folder,
                                                             message=message))
        except (MPValidationException, ValidationError) as validation_exception:
            logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mp_folder,
                                                             message=f"Mapping package is not valid: {validation_exception}"))
            all_valid = False

    return all_valid


@traced_routine
def validate_bulk_mapping_packages_from_github(
        github_repository_url: str,
        packages_path_pattern: str,
        branch_or_tag_name: Optional[str] = None,
        github_package_extractor: Optional[GithubPackageExtractor] = None,
        mapping_package_loader: MappingPackageAssetLoader = None,
        mp_validator: Optional[MappingPackageValidator] = None) -> NoReturn:
    if not github_repository_url:
        message: str = "Cannot validate packages from github. Repository URL is empty"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source="github", message=message))
        raise ValueError(message)

    if not packages_path_pattern:
        message: str = "Cannot validate packages from github. Packages path pattern is empty"
        logger.error(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source="github", message=message))
        raise ValueError(message)

    logger.info(MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=f"URL: {github_repository_url} | branch_or_tag_name: {branch_or_tag_name} | pattern: {packages_path_pattern}",
        message=f"Validating bulk mapping packages from Github"))

    mapping_packages: List[MappingPackage] = load_mapping_packages_from_github(
        github_repository_url=github_repository_url,
        packages_path_pattern=packages_path_pattern,
        branch_or_tag_name=branch_or_tag_name,
        github_package_extractor=github_package_extractor,
        mapping_package_loader=mapping_package_loader)

    for mapping_package in mapping_packages:
        try:
            validate_mapping_package(mapping_package=mapping_package, mp_validator=mp_validator)
        except MPValidationException as validation_exception:
            logger.warning(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package.metadata.identifier,
                                                               message=f"Mapping package is not valid: {validation_exception}"))
        else:
            logger.info(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package.metadata.identifier,
                                                            message=f"✅ The package is valid!"))
