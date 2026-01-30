from pathlib import Path
from unittest.mock import patch

import pytest

from mapping_suite_sdk.core.adapters.validator import MPValidationException
from mapping_suite_sdk.tools.services.validate_mapping_package import (
    CrossVersionValidationError,
    validate_mapping_package,
)


def test_validate_mapping_package_auto_detects_version_for_folder_path(tmp_path: Path) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value="v2") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder", return_value=True) as mock_v2,
    ):
        assert validate_mapping_package(tmp_path) is True
        mock_detect.assert_called_once_with(tmp_path)
        mock_v2.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_mapping_package_explicit_version_skips_detection_for_folder_path(tmp_path: Path) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder", return_value=True) as mock_v3,
    ):
        assert validate_mapping_package(tmp_path, version="v3") is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once_with(mapping_package_folder_path=tmp_path)


def test_validate_mapping_package_raises_clear_error_for_unknown_version(tmp_path: Path) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=None),
    ):
        with pytest.raises(CrossVersionValidationError, match="Unknown or unsupported mapping package version"):
            validate_mapping_package(tmp_path)


def test_validate_mapping_package_archive_does_not_wrap_validation_errors(tmp_path: Path) -> None:
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")  # just needs to exist as a file for this test

    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract", return_value=tmp_path / "extracted") as mock_extract,
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value="v3L"),
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight_from_folder",
            side_effect=MPValidationException("Hash validation failed"),
        ),
    ):
        with pytest.raises(MPValidationException, match="Hash validation failed"):
            validate_mapping_package(archive_path)
        mock_extract.assert_called_once()


def test_validate_mapping_package_auto_detects_version_from_model_type(dummy_mapping_package_v1_model) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1", return_value=True) as mock_v1,
    ):
        assert validate_mapping_package(dummy_mapping_package_v1_model) is True
        mock_detect.assert_not_called()
        mock_v1.assert_called_once()


def test_validate_mapping_package_explicit_version_skips_detection_for_model(fixture_mapping_package_v3_model) -> None:
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3", return_value=True) as mock_v3,
    ):
        assert validate_mapping_package(fixture_mapping_package_v3_model, version="v3") is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once()

