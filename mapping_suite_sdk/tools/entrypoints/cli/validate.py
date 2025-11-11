import logging
from pathlib import Path

import typer

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.tools.entrypoints.cli import typer_verbose_callback, MappingPackageVersion
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import MappingPackageV1Loader
from mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1 import \
    validate_mapping_package_v1_from_archive, validate_bulk_mapping_packages_v1_from_github, \
    validate_bulk_mapping_packages_v1_from_folder
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2 import \
    validate_mapping_package_v2_from_archive, validate_bulk_mapping_packages_v2_from_github, \
    validate_bulk_mapping_packages_v2_from_folder
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader_lightweight import MappingPackageV3LightweightLoader
from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3 import \
    validate_mapping_package_v3_from_archive, validate_bulk_mapping_packages_v3_from_github, \
    validate_bulk_mapping_packages_v3_from_folder
from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight import \
    validate_mapping_package_v3_lightweight_from_archive, \
    validate_bulk_mapping_packages_v3_lightweight_from_github, \
    validate_bulk_mapping_packages_v3_lightweight_from_folder

logger = logging.getLogger(__name__)

# Constants for repeated string literals
_ERROR_VERSION_CHECKING = "Something went wrong package version checking callback."

mssdk_cli_validate_subcommand = typer.Typer(**mssdk_config.MSSDK_TYPER_DEFAULT_ARGS,
                                            name="validate",
                                            help="Mapping Package Validation commands.")


@mssdk_cli_validate_subcommand.callback()
def validate_common(
        ctx: typer.Context,
        version: str = typer.Option(..., "--version", help=f"Package version ({MappingPackageVersion.list()})")
):
    """Set validation version context."""
    mapping_package_versions = MappingPackageVersion.list()
    if version not in mapping_package_versions:
        raise typer.BadParameter(f"Version must be {mapping_package_versions}, got: {version}")

    ctx.ensure_object(dict)
    ctx.obj['version'] = version


@mssdk_cli_validate_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                       name="from-archive",
                                       help="Validate archive.")
def mssdk_cli_validate_mapping_package_from_archive(
        ctx: typer.Context,
        mapping_package_archive_path: Path = typer.Argument(..., exists=True),
        include_test_data: bool = typer.Option(False, "--include-test-data"),
        include_output: bool = typer.Option(False, "--include-output"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Validate archive."""
    version = ctx.obj['version']

    logger.debug(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_archive_path,
        message=f"Validating {version} package from archive"))

    if version == MappingPackageVersion.V1:
        loader = MappingPackageV1Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_mapping_package_v1_from_archive(
            mapping_package_archive_path=mapping_package_archive_path,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V2:
        loader = MappingPackageV2Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_mapping_package_v2_from_archive(
            mapping_package_archive_path=mapping_package_archive_path,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V3:
        loader = MappingPackageV3Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_mapping_package_v3_from_archive(
            mapping_package_archive_path=mapping_package_archive_path,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V3_LIGHTWEIGHT:
        loader = MappingPackageV3LightweightLoader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_mapping_package_v3_lightweight_from_archive(
            mapping_package_archive_path=mapping_package_archive_path,
            mapping_package_loader=loader)

    else:
        raise typer.BadParameter(_ERROR_VERSION_CHECKING)

    status = "✅ Valid" if all_valid else "❌ Invalid"
    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=mapping_package_archive_path,
        message=f"{status} {version} package"))

    if not all_valid:
        raise typer.Exit(code=1)


@mssdk_cli_validate_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                       name="from-github",
                                       help="Validate packages from GitHub.")
def mssdk_cli_validate_mapping_packages_from_github(
        ctx: typer.Context,
        github_repository_url: str = typer.Argument(...),
        packages_path_pattern: str = typer.Argument(...),
        include_test_data: bool = typer.Option(False, "--include-test-data"),
        include_output: bool = typer.Option(False, "--include-output"),
        branch_or_tag_name: str = typer.Option(None, "--branch", "-b"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Validate packages from GitHub."""
    version = ctx.obj['version']

    if version == MappingPackageVersion.V1:
        loader = MappingPackageV1Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v1_from_github(
            github_repository_url=github_repository_url,
            packages_path_pattern=packages_path_pattern,
            branch_or_tag_name=branch_or_tag_name,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V2:
        loader = MappingPackageV2Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v2_from_github(
            github_repository_url=github_repository_url,
            packages_path_pattern=packages_path_pattern,
            branch_or_tag_name=branch_or_tag_name,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V3:
        loader = MappingPackageV3Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=github_repository_url,
            packages_path_pattern=packages_path_pattern,
            branch_or_tag_name=branch_or_tag_name,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V3_LIGHTWEIGHT:
        loader = MappingPackageV3LightweightLoader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v3_lightweight_from_github(
            github_repository_url=github_repository_url,
            packages_path_pattern=packages_path_pattern,
            branch_or_tag_name=branch_or_tag_name,
            mapping_package_loader=loader)

    else:
        raise typer.BadParameter(_ERROR_VERSION_CHECKING)

    if not all_valid:
        raise typer.Exit(code=1)


@mssdk_cli_validate_subcommand.command(**mssdk_config.MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                       name="from-folder",
                                       help="Validate packages from folder.")
def mssdk_cli_validate_mapping_packages_from_folder(
        ctx: typer.Context,
        folder_path: Path = typer.Argument(...),
        update_hash: bool = typer.Option(False, "--update-hash", "-u"),
        include_test_data: bool = typer.Option(False, "--include-test-data"),
        include_output: bool = typer.Option(False, "--include-output"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback),
) -> None:
    """Validate packages from folder."""
    version = ctx.obj['version']

    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"Validating {version} packages from folder"))

    if version == MappingPackageVersion.V1:
        loader = MappingPackageV1Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v1_from_folder(
            mapping_packages_folder_path=folder_path,
            update_hash=update_hash,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V2:
        loader = MappingPackageV2Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v2_from_folder(
            mapping_packages_folder_path=folder_path,
            update_hash=update_hash,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V3:
        loader = MappingPackageV3Loader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v3_from_folder(
            mapping_packages_folder_path=folder_path,
            update_hash=update_hash,
            mapping_package_loader=loader)
    elif version == MappingPackageVersion.V3_LIGHTWEIGHT:
        loader = MappingPackageV3LightweightLoader(include_test_data=include_test_data, include_output=include_output)
        all_valid = validate_bulk_mapping_packages_v3_lightweight_from_folder(
            mapping_packages_folder_path=folder_path,
            update_hash=update_hash,
            mapping_package_loader=loader)

    else:
        raise typer.BadParameter(_ERROR_VERSION_CHECKING)

    status = "✅ All valid" if all_valid else "❌ Invalid packages found"
    logger.info(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
        package_source=folder_path,
        message=f"{status} {version} packages"))

    if not all_valid:
        raise typer.Exit(code=1)
