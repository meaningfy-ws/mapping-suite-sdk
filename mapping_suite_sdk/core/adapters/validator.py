import logging
from abc import ABC, abstractmethod
from pathlib import Path
from types import FunctionType
from typing import Optional, Literal, NoReturn, Any

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.models.mapping_package import MappingPackage

logger = logging.getLogger(__name__)


class MPValidationException(Exception): pass


def warn_on_empty_test_result_suites(mapping_package: Any) -> None:
    """
    Emit warnings (not errors) for empty/unexpected test result suites.

    Outputs (test results) are not required for a mapping package to be loadable/processable.
    Some production packages may contain partial or unexpected output structures; we warn
    to surface the issue without blocking validation.
    """
    test_results = getattr(mapping_package, "test_results", None)
    if not test_results:
        return

    suites = getattr(test_results, "result_suites", None) or []
    for suite in suites:
        if not getattr(suite, "files", None):
            suite_path = getattr(suite, "path", "<unknown>")
            logger.warning(
                "Mapping Package structural warning: empty test result suite at %s",
                suite_path,
            )


def validate_next(func: FunctionType):
    """Decorator implementing chain-of-responsibility pattern for validation.

    After executing the current validation step, automatically invokes the next
    validator in the chain (if one exists). This enables composable validation:

    Example:
        >>> hash_validator = MPV3HashValidationStep(
        ...     next_validator=MPV3StructuralValidationStep()
        ... )
        >>> hash_validator.validate(package)  # Runs both validators in sequence
    """
    def wrapper(self, mapping_package: MappingPackage):
        result = func(self, mapping_package)
        if self.next_validator:
            return self.next_validator.validate(mapping_package)
        return result

    return wrapper


class MPValidationStepABC(ABC):
    """Abstract base class for Mapping Package validation steps.

    Implements the chain-of-responsibility pattern for composable validation.
    Provides validation helper utilities as static methods for consistent
    path and parameter validation across all mapping package versions.

    Attributes:
        next_validator (Optional[MPValidationStepABC]): The next validation step in the chain.

    Methods:
        validate(mapping_package: MappingPackage) -> Literal[True] | NoReturn:
            Validates the given Mapping Package. If the validation passes, it returns True.
            If the validation fails, it raises an exception.

    Static Validation Helpers:
        validate_path_exists: Validate that a path exists
        validate_is_file: Validate that a path is a file
        validate_is_directory: Validate that a path is a directory
        validate_folder_path: Validate path exists and is a directory
        validate_archive_path: Validate path exists and is a file
        validate_string_parameter: Validate string parameter is not empty
    """

    def __init__(self, next_validator: Optional["MPValidationStepABC"] = None):
        self.next_validator = next_validator

    @abstractmethod
    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        raise NotImplementedError

    # ========== Validation Helper Methods ==========
    # These static methods provide reusable validation logic to reduce
    # code duplication across all mapping package version validators.

    @staticmethod
    def validate_path_exists(path: Path, context: str) -> None:
        """Validate that a path exists and log error if not.

        Args:
            path: Path to validate
            context: Context description (e.g., "folder", "archive", "package")

        Raises:
            FileNotFoundError: If the path does not exist

        Example:
            >>> MPValidationStepABC.validate_path_exists(Path("/path/to/package"), "package folder")
        """
        if not path.exists():
            message = f"Cannot process {context}. Path does not exist: {path}"
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=path, message=message))
            raise FileNotFoundError(message)

    @staticmethod
    def validate_is_file(path: Path, context: str) -> None:
        """Validate that a path is a file and log error if not.

        Args:
            path: Path to validate
            context: Context description for error message

        Raises:
            ValueError: If the path is not a file

        Example:
            >>> MPValidationStepABC.validate_is_file(Path("/path/to/archive.zip"), "archive")
        """
        if not path.is_file():
            message = f"Cannot process {context}. Path is not a file: {path}"
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=path, message=message))
            raise ValueError(message)

    @staticmethod
    def validate_is_directory(path: Path, context: str) -> None:
        """Validate that a path is a directory and log error if not.

        Args:
            path: Path to validate
            context: Context description for error message

        Raises:
            NotADirectoryError: If the path is not a directory

        Example:
            >>> MPValidationStepABC.validate_is_directory(Path("/path/to/folder"), "package folder")
        """
        if not path.is_dir():
            message = f"Cannot process {context}. Path is not a directory: {path}"
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=path, message=message))
            raise NotADirectoryError(message)

    @staticmethod
    def validate_folder_path(path: Path, context: str = "folder") -> None:
        """Validate that a path exists and is a directory.

        Combines path existence and directory type validation in a single call.

        Args:
            path: Path to validate
            context: Context description for error messages

        Raises:
            FileNotFoundError: If the path does not exist
            NotADirectoryError: If the path is not a directory

        Example:
            >>> MPValidationStepABC.validate_folder_path(Path("/packages/v1"), "package folder")
        """
        MPValidationStepABC.validate_path_exists(path, context)
        MPValidationStepABC.validate_is_directory(path, context)

    @staticmethod
    def validate_archive_path(path: Path, context: str = "archive") -> None:
        """Validate that a path exists and is a file.

        Combines path existence and file type validation in a single call.

        Args:
            path: Path to validate
            context: Context description for error messages

        Raises:
            FileNotFoundError: If the path does not exist
            ValueError: If the path is not a file

        Example:
            >>> MPValidationStepABC.validate_archive_path(Path("/packages/v1.zip"), "package archive")
        """
        MPValidationStepABC.validate_path_exists(path, context)
        MPValidationStepABC.validate_is_file(path, context)

    @staticmethod
    def validate_string_parameter(value: str | None, param_name: str, context: str) -> None:
        """Validate that a string parameter is not empty or None.

        Args:
            value: String value to validate
            param_name: Name of the parameter for error message
            context: Context description for error message (e.g., "validate packages from github")

        Raises:
            ValueError: If the value is empty or None

        Example:
            >>> MPValidationStepABC.validate_string_parameter(repo_url, "Repository URL", "load from github")
        """
        if not value:
            message = f"Cannot {context}. {param_name} is empty"
            logger.error(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(
                package_source=context, message=message))
            raise ValueError(message)
