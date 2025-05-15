import logging
from pathlib import Path

import typer

from mapping_suite_sdk import validate_mapping_package_from_archive, validate_bulk_mapping_packages_from_github, \
    validate_bulk_mapping_packages_from_folder
from mapping_suite_sdk.entrypoints.cli import typer_verbose_callback
from mapping_suite_sdk.vars import MSSDK_TYPER_DEFAULT_ARGS, MSSDK_TYPER_COMMANDS_DEFAULT_ARGS, \
    MSSDK_LOGGING_MESSAGE_FORMAT

logger = logging.getLogger(__name__)

mssdk_cli_validate_subcommand = typer.Typer(**MSSDK_TYPER_DEFAULT_ARGS,
                                            name="validate",
                                            help="Mapping Package Validation-related commands.")


@mssdk_cli_validate_subcommand.command(**MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                       name="from-archive",
                                       help="Validate a single archive.")
def mssdk_cli_validate_mapping_package_from_archive(
        mapping_package_archive_path: Path = typer.Argument(..., exists=True),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback,
                                     help="Show debug logs."),
) -> None:
    """Validate a single archive."""
    logger.debug(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=mapping_package_archive_path,
                                                     message="Running mapping package validation from archive using command line"))

    validate_mapping_package_from_archive(mapping_package_archive_path=mapping_package_archive_path)


@mssdk_cli_validate_subcommand.command(**MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                       name="from-github",
                                       help="Validate a list of mapping packages folders from GitHub.")
def mssdk_cli_validate_mapping_packages_from_github(
        github_repository_url: str = typer.Argument(..., help="GitHub repository URL"),
        packages_path_pattern: str = typer.Argument(..., help="Package path pattern. Example: mappings/*"),
        branch_or_tag_name: str = typer.Option(None, "--branch", "-b", help="Branch or tag name"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback,
                                     help="Show debug logs."),
) -> None:
    """Validate mapping packages from GitHub repository."""
    validate_bulk_mapping_packages_from_github(
        github_repository_url=github_repository_url,
        packages_path_pattern=packages_path_pattern,
        branch_or_tag_name=branch_or_tag_name
    )


@mssdk_cli_validate_subcommand.command(**MSSDK_TYPER_COMMANDS_DEFAULT_ARGS,
                                       name="from-folder",
                                       help="Validate a list of mapping packages folders from folder.")
def mssdk_cli_validate_mapping_packages_from_folder(
        folder_path: Path = typer.Argument(..., help="Folder containing mapping packages folders. Example: mappings/"),
        update_hash: bool = typer.Option(False, "--update-hash", "-u", help="Update hash for packages that has invalid hash."),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     is_eager=True,
                                     callback=typer_verbose_callback,
                                     help="Show debug logs."),
) -> None:
    """Validate mapping packages from folder."""
    logger.info(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=folder_path, message="Running mapping package validation from folder using command line"))

    all_valid: bool = validate_bulk_mapping_packages_from_folder(mapping_packages_folder_path=folder_path, update_hash=update_hash)
    if all_valid:
        logger.info(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=folder_path, message="Running mapping package validation from folder using command line finished successfully.\n✅ All packages are valid!"))
    else:
        logger.info(MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=folder_path, message="Running mapping package validation from folder using command line finished successfully.\n❌ There are invalid packages! Please check the logs."))
