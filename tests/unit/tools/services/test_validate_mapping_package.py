from pathlib import Path
from unittest.mock import patch

import pytest
from typing import cast

from mapping_suite_sdk.core.adapters.validator import MPValidationException
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import MappingPackageV1Loader
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import MappingPackageV3LightweightLoader
from mapping_suite_sdk.tools.services.convert_mapping_package import Version
from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import (
    convert_mapping_package_v3_to_v3_lightweight,
)
from mapping_suite_sdk.tools.services.validate_mapping_package import (
    CrossVersionValidationError,
    _normalize_version,
    _validate_folder_from_path,
    _validate_model,
    _detect_version_from_model,
    validate_mapping_package,
)


def _assert_loader(mock_call, expected_loader_type, include_test_data=False, include_output=False):
    """Assert loader type and configuration in mock call."""
    loader = mock_call.call_args.kwargs["mapping_package_loader"]
    assert isinstance(loader, expected_loader_type), f"Expected {expected_loader_type}, got {type(loader)}"
    assert loader.include_test_data == include_test_data
    assert loader.include_output == include_output


def test_validate_mapping_package_auto_detects_version_for_folder_path(tmp_path: Path) -> None:
    """Test that version is auto-detected when validating a folder path without explicit version."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=Version.V2) as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder", return_value=True) as mock_v2,
    ):
        assert validate_mapping_package(tmp_path) is True
        mock_detect.assert_called_once_with(tmp_path)
        mock_v2.assert_called_once()
        assert mock_v2.call_args.kwargs["mapping_package_folder_path"] == tmp_path
        _assert_loader(mock_v2, MappingPackageV2Loader, include_test_data=False, include_output=False)


def test_validate_mapping_package_explicit_version_skips_detection_for_folder_path(tmp_path: Path) -> None:
    """Test that explicit version parameter skips auto-detection for folder paths."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder", return_value=True) as mock_v3,
    ):
        assert validate_mapping_package(tmp_path, version="v3") is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once()
        assert mock_v3.call_args.kwargs["mapping_package_folder_path"] == tmp_path
        _assert_loader(mock_v3, MappingPackageV3Loader, include_test_data=False, include_output=False)


def test_validate_mapping_package_raises_clear_error_for_unknown_version(tmp_path: Path) -> None:
    """Test that a clear error is raised when version cannot be detected."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=None),
    ):
        with pytest.raises(CrossVersionValidationError, match="Unknown or unsupported mapping package version"):
            validate_mapping_package(tmp_path)


def test_validate_mapping_package_archive_does_not_wrap_validation_errors(tmp_path: Path) -> None:
    """Test that validation errors from archive extraction are propagated without wrapping."""
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")  # just needs to exist as a file for this test

    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract", return_value=tmp_path / "extracted") as mock_extract,
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version", return_value=Version.V3L),
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight_from_folder",
            side_effect=MPValidationException("Hash validation failed"),
        ),
    ):
        with pytest.raises(MPValidationException, match="Hash validation failed"):
            validate_mapping_package(archive_path)
        mock_extract.assert_called_once()


def test_validate_mapping_package_auto_detects_version_from_model_type(dummy_mapping_package_v1_model) -> None:
    """Test that version is auto-detected from model type when validating a model instance."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1", return_value=True) as mock_v1,
    ):
        assert validate_mapping_package(dummy_mapping_package_v1_model) is True
        mock_detect.assert_not_called()
        mock_v1.assert_called_once()


def test_validate_mapping_package_explicit_version_skips_detection_for_model(fixture_mapping_package_v3_model) -> None:
    """Test that explicit version parameter skips auto-detection for model instances."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch("mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3", return_value=True) as mock_v3,
    ):
        assert validate_mapping_package(fixture_mapping_package_v3_model, version="v3") is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once()


# --- _normalize_version ---


def test_normalize_version_strips_whitespace() -> None:
    """Test that _normalize_version strips leading and trailing whitespace."""
    assert _normalize_version("  v1  ") == Version.V1


def test_normalize_version_lowercases() -> None:
    """Test that _normalize_version converts version strings to lowercase."""
    assert _normalize_version("V1") == Version.V1
    assert _normalize_version("V2") == Version.V2
    assert _normalize_version("V3") == Version.V3


def test_normalize_version_v3l_to_v3L() -> None:
    """Test that _normalize_version correctly handles v3L case variations."""
    assert _normalize_version("v3l") == Version.V3L
    assert _normalize_version("V3L") == Version.V3L
    assert _normalize_version("  v3l  ") == Version.V3L


def test_normalize_version_raises_on_invalid_version() -> None:
    """Test that _normalize_version raises CrossVersionValidationError for invalid versions."""
    with pytest.raises(CrossVersionValidationError, match="Unsupported version: v99"):
        _normalize_version("v99")


# --- _validate_model ---


def test_validate_model_v1_calls_v1_validator(dummy_mapping_package_v1_model) -> None:
    """Test that _validate_model calls the V1 validator for V1 models."""
    with patch(
        "mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1",
        return_value=True,
    ) as mock_v1:
        assert _validate_model(dummy_mapping_package_v1_model, Version.V1) is True
        mock_v1.assert_called_once_with(mapping_package=dummy_mapping_package_v1_model)


def test_validate_model_v1_raises_on_wrong_type(fixture_mapping_package_v3_model) -> None:
    """Test that _validate_model raises error when model type doesn't match V1."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v1' requires MappingPackageV1"):
        _validate_model(fixture_mapping_package_v3_model, Version.V1)


def test_validate_model_v2_calls_v2_validator(dummy_mapping_package_v2_model) -> None:
    """Test that _validate_model calls the V2 validator for V2 models."""
    with patch(
        "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2",
        return_value=True,
    ) as mock_v2:
        assert _validate_model(dummy_mapping_package_v2_model, Version.V2) is True
        mock_v2.assert_called_once_with(mapping_package=dummy_mapping_package_v2_model)


def test_validate_model_v2_raises_on_wrong_type(dummy_mapping_package_v1_model) -> None:
    """Test that _validate_model raises error when model type doesn't match V2."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v2' requires MappingPackageV2"):
        _validate_model(dummy_mapping_package_v1_model, Version.V2)


def test_validate_model_v3_calls_v3_validator(fixture_mapping_package_v3_model) -> None:
    """Test that _validate_model calls the V3 validator for V3 models."""
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3",
        return_value=True,
    ) as mock_v3:
        assert _validate_model(fixture_mapping_package_v3_model, Version.V3) is True
        mock_v3.assert_called_once_with(mapping_package=fixture_mapping_package_v3_model)


def test_validate_model_v3_raises_on_wrong_type(dummy_mapping_package_v1_model) -> None:
    """Test that _validate_model raises error when model type doesn't match V3."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v3' requires MappingPackageV3"):
        _validate_model(dummy_mapping_package_v1_model, Version.V3)


def test_validate_model_v3L_calls_v3_lightweight_validator(
    fixture_mapping_package_v3_model,
) -> None:
    """Test that _validate_model calls the V3 Lightweight validator for V3L models."""
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight",
        return_value=True,
    ) as mock_v3l:
        assert _validate_model(v3l_model, Version.V3L) is True
        mock_v3l.assert_called_once_with(mapping_package=v3l_model)


def test_validate_model_v3L_raises_on_wrong_type(fixture_mapping_package_v3_model) -> None:
    """Test that _validate_model raises error when model type doesn't match V3L."""
    with pytest.raises(
        CrossVersionValidationError,
        match="Version 'v3L' requires MappingPackageV3Lightweight",
    ):
        _validate_model(fixture_mapping_package_v3_model, Version.V3L)


def test_validate_model_raises_on_unsupported_version(dummy_mapping_package_v1_model) -> None:
    """Test that _validate_model raises error for unsupported version strings."""
    with pytest.raises(CrossVersionValidationError, match="Unsupported version"):
        _validate_model(dummy_mapping_package_v1_model, cast(Version, "v99"))


# --- _validate_folder_from_path ---


def test_validate_folder_from_path_v1_calls_v1_from_folder(tmp_path: Path) -> None:
    """Test that _validate_folder_from_path calls V1 folder validator for V1 version."""
    with patch(
        "mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1.validate_mapping_package_v1_from_folder",
        return_value=True,
    ) as mock_v1:
        assert _validate_folder_from_path(tmp_path, Version.V1) is True
        mock_v1.assert_called_once()
        assert mock_v1.call_args.kwargs["mapping_package_folder_path"] == tmp_path
        _assert_loader(mock_v1, MappingPackageV1Loader, include_test_data=False, include_output=False)


def test_validate_folder_from_path_v2_calls_v2_from_folder(tmp_path: Path) -> None:
    """Test that _validate_folder_from_path calls V2 folder validator for V2 version."""
    with patch(
        "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder",
        return_value=True,
    ) as mock_v2:
        assert _validate_folder_from_path(tmp_path, Version.V2) is True
        mock_v2.assert_called_once()
        assert mock_v2.call_args.kwargs["mapping_package_folder_path"] == tmp_path
        _assert_loader(mock_v2, MappingPackageV2Loader, include_test_data=False, include_output=False)


def test_validate_folder_from_path_v3_calls_v3_from_folder(tmp_path: Path) -> None:
    """Test that _validate_folder_from_path calls V3 folder validator for V3 version."""
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder",
        return_value=True,
    ) as mock_v3:
        assert _validate_folder_from_path(tmp_path, Version.V3) is True
        mock_v3.assert_called_once()
        assert mock_v3.call_args.kwargs["mapping_package_folder_path"] == tmp_path
        _assert_loader(mock_v3, MappingPackageV3Loader, include_test_data=False, include_output=False)


def test_validate_folder_from_path_v3L_calls_v3_lightweight_from_folder(tmp_path: Path) -> None:
    """Test that _validate_folder_from_path calls V3L folder validator for V3L version."""
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight_from_folder",
        return_value=True,
    ) as mock_v3l:
        assert _validate_folder_from_path(tmp_path, Version.V3L) is True
        mock_v3l.assert_called_once()
        assert mock_v3l.call_args.kwargs["mapping_package_folder_path"] == tmp_path
        _assert_loader(mock_v3l, MappingPackageV3LightweightLoader, include_test_data=False, include_output=False)


def test_validate_folder_from_path_propagates_include_test_data(tmp_path: Path) -> None:
    """Test that include_test_data is propagated to the loader."""
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder",
        return_value=True,
    ) as mock_v3:
        assert _validate_folder_from_path(tmp_path, Version.V3, include_test_data=True) is True
        _assert_loader(mock_v3, MappingPackageV3Loader, include_test_data=True, include_output=False)


def test_validate_folder_from_path_propagates_include_output(tmp_path: Path) -> None:
    """Test that include_output is propagated to the loader."""
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder",
        return_value=True,
    ) as mock_v3:
        assert _validate_folder_from_path(tmp_path, Version.V3, include_output=True) is True
        _assert_loader(mock_v3, MappingPackageV3Loader, include_test_data=False, include_output=True)


def test_validate_folder_from_path_propagates_both_flags(tmp_path: Path) -> None:
    """Test that both include_test_data and include_output are propagated to the loader."""
    with patch(
        "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder",
        return_value=True,
    ) as mock_v2:
        assert _validate_folder_from_path(tmp_path, Version.V2, include_test_data=True, include_output=True) is True
        _assert_loader(mock_v2, MappingPackageV2Loader, include_test_data=True, include_output=True)


def test_validate_mapping_package_propagates_flags_to_folder_validation(tmp_path: Path) -> None:
    """Test that validate_mapping_package propagates include_test_data and include_output to folder validation."""
    with patch(
        "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder",
        return_value=True,
    ) as mock_v3:
        assert validate_mapping_package(tmp_path, version="v3", include_test_data=True, include_output=True) is True
        _assert_loader(mock_v3, MappingPackageV3Loader, include_test_data=True, include_output=True)


# --- _detect_version_from_model ---


def test_detect_version_from_model_v1(dummy_mapping_package_v1_model) -> None:
    """Test that _detect_version_from_model correctly identifies V1 models."""
    assert _detect_version_from_model(dummy_mapping_package_v1_model) == Version.V1


def test_detect_version_from_model_v2(dummy_mapping_package_v2_model) -> None:
    """Test that _detect_version_from_model correctly identifies V2 models."""
    assert _detect_version_from_model(dummy_mapping_package_v2_model) == Version.V2


def test_detect_version_from_model_v3(fixture_mapping_package_v3_model) -> None:
    """Test that _detect_version_from_model correctly identifies V3 models."""
    assert _detect_version_from_model(fixture_mapping_package_v3_model) == Version.V3


def test_detect_version_from_model_v3L(fixture_mapping_package_v3_model) -> None:
    """Test that _detect_version_from_model correctly identifies V3L models."""
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    assert _detect_version_from_model(v3l_model) == Version.V3L


def test_detect_version_from_model_raises_for_unknown_type() -> None:
    """Test that _detect_version_from_model raises error for unrecognized model types."""
    with pytest.raises(CrossVersionValidationError, match="Cannot auto-detect version"):
        _detect_version_from_model("not a package")


# --- validate_mapping_package: archive + unknown version ---


def test_validate_mapping_package_archive_raises_clear_error_for_unknown_version(tmp_path: Path) -> None:
    """Test that archive validation raises clear error when version cannot be detected."""
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract",
            return_value=tmp_path / "extracted",
        ),
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
            return_value=None,
        ),
    ):
        with pytest.raises(CrossVersionValidationError, match="Unknown or unsupported mapping package version"):
            validate_mapping_package(archive_path)


# --- validate_mapping_package: auto-detect from model type ---


def test_validate_mapping_package_auto_detects_v2_from_model_type(dummy_mapping_package_v2_model) -> None:
    """Test that version is auto-detected from V2 model type."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2",
            return_value=True,
        ) as mock_v2,
    ):
        assert validate_mapping_package(dummy_mapping_package_v2_model) is True
        mock_detect.assert_not_called()
        mock_v2.assert_called_once_with(mapping_package=dummy_mapping_package_v2_model)


def test_validate_mapping_package_auto_detects_v3L_from_model_type(
    fixture_mapping_package_v3_model,
) -> None:
    """Test that version is auto-detected from V3L model type."""
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight.validate_mapping_package_v3_lightweight",
            return_value=True,
        ) as mock_v3l,
    ):
        assert validate_mapping_package(v3l_model) is True
        mock_detect.assert_not_called()
        mock_v3l.assert_called_once_with(mapping_package=v3l_model)


def test_validate_mapping_package_auto_detects_v3_from_model_type(fixture_mapping_package_v3_model) -> None:
    """Test that version is auto-detected from V3 model type."""
    with (
        patch("mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version") as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3",
            return_value=True,
        ) as mock_v3,
    ):
        assert validate_mapping_package(fixture_mapping_package_v3_model) is True
        mock_detect.assert_not_called()
        mock_v3.assert_called_once_with(mapping_package=fixture_mapping_package_v3_model)


def test_validate_mapping_package_raises_when_model_type_unknown() -> None:
    """Test that error is raised when model type cannot be determined."""
    with pytest.raises(
        CrossVersionValidationError,
        match="Cannot auto-detect version from mapping package type",
    ):
        validate_mapping_package("not a package")


def test_validate_mapping_package_raises_on_explicit_unsupported_version_for_path(tmp_path: Path) -> None:
    """Test that an explicit unsupported version string raises clearly for folder path."""
    with pytest.raises(CrossVersionValidationError, match="Unsupported version: v99"):
        validate_mapping_package(tmp_path, version="v99")


def test_validate_mapping_package_raises_on_explicit_unsupported_version_for_model(dummy_mapping_package_v1_model) -> None:
    """Test that an explicit unsupported version string raises clearly for model instance."""
    with pytest.raises(CrossVersionValidationError, match="Unsupported version: v99"):
        validate_mapping_package(dummy_mapping_package_v1_model, version="v99")


def test_validate_folder_from_path_raises_on_unsupported_version(tmp_path: Path) -> None:
    """Test that _validate_folder_from_path raises for unsupported version."""
    with pytest.raises(CrossVersionValidationError, match="Unsupported version"):
        _validate_folder_from_path(tmp_path, cast(Version, "v99"))

def test_validate_mapping_package_archive_succeeds_with_auto_detection(tmp_path: Path) -> None:
    """Test that archive validation succeeds when auto-detection works and validation passes."""
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")
    extracted_path = tmp_path / "extracted"
    extracted_path.mkdir()

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract",
            return_value=extracted_path,
        ) as mock_extract,
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
            return_value=Version.V2,
        ) as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder",
            return_value=True,
        ) as mock_v2,
    ):
        assert validate_mapping_package(archive_path) is True

        # Verify extract was called with archive_path as first arg
        assert mock_extract.call_count == 1
        call_args = mock_extract.call_args[0]
        assert call_args[0] == archive_path

        mock_detect.assert_called_once_with(extracted_path)
        mock_v2.assert_called_once()
        assert mock_v2.call_args.kwargs["mapping_package_folder_path"] == extracted_path
        _assert_loader(mock_v2, MappingPackageV2Loader, include_test_data=False, include_output=False)


def test_validate_mapping_package_archive_succeeds_with_explicit_version(tmp_path: Path) -> None:
    """Test that archive validation with explicit version skips auto-detection."""
    archive_path = tmp_path / "mp.zip"
    archive_path.write_text("dummy")
    extracted_path = tmp_path / "extracted"
    extracted_path.mkdir()

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract",
            return_value=extracted_path,
        ) as mock_extract,
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
        ) as mock_detect,
        patch(
            "mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3.validate_mapping_package_v3_from_folder",
            return_value=True,
        ) as mock_v3,
    ):
        assert validate_mapping_package(archive_path, version="v3") is True

        # Verify extract was called with archive_path as first arg
        assert mock_extract.call_count == 1
        call_args = mock_extract.call_args[0]
        assert call_args[0] == archive_path

        mock_detect.assert_not_called()
        mock_v3.assert_called_once()
        assert mock_v3.call_args.kwargs["mapping_package_folder_path"] == extracted_path
        _assert_loader(mock_v3, MappingPackageV3Loader, include_test_data=False, include_output=False)


# --- validate_mapping_package: model validation ---


def test_validate_mapping_package_raises_on_model_version_mismatch_v1_to_v2(dummy_mapping_package_v1_model) -> None:
    """Test that providing V1 model with version='v2' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v2' requires MappingPackageV2"):
        validate_mapping_package(dummy_mapping_package_v1_model, version="v2")


def test_validate_mapping_package_raises_on_model_version_mismatch_v1_to_v3(dummy_mapping_package_v1_model) -> None:
    """Test that providing V1 model with version='v3' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v3' requires MappingPackageV3"):
        validate_mapping_package(dummy_mapping_package_v1_model, version="v3")


def test_validate_mapping_package_raises_on_model_version_mismatch_v2_to_v1(dummy_mapping_package_v2_model) -> None:
    """Test that providing V2 model with version='v1' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v1' requires MappingPackageV1"):
        validate_mapping_package(dummy_mapping_package_v2_model, version="v1")


def test_validate_mapping_package_raises_on_model_version_mismatch_v2_to_v3(dummy_mapping_package_v2_model) -> None:
    """Test that providing V2 model with version='v3' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v3' requires MappingPackageV3"):
        validate_mapping_package(dummy_mapping_package_v2_model, version="v3")


def test_validate_mapping_package_raises_on_model_version_mismatch_v3_to_v1(fixture_mapping_package_v3_model) -> None:
    """Test that providing V3 model with version='v1' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v1' requires MappingPackageV1"):
        validate_mapping_package(fixture_mapping_package_v3_model, version="v1")


def test_validate_mapping_package_raises_on_model_version_mismatch_v3_to_v2(fixture_mapping_package_v3_model) -> None:
    """Test that providing V3 model with version='v2' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v2' requires MappingPackageV2"):
        validate_mapping_package(fixture_mapping_package_v3_model, version="v2")


def test_validate_mapping_package_raises_on_model_version_mismatch_v3_to_v3L(fixture_mapping_package_v3_model) -> None:
    """Test that providing V3 model with version='v3L' raises."""
    with pytest.raises(CrossVersionValidationError, match="Version 'v3L' requires MappingPackageV3Lightweight"):
        validate_mapping_package(fixture_mapping_package_v3_model, version="v3L")


def test_validate_mapping_package_raises_on_model_version_mismatch_v3L_to_v3(fixture_mapping_package_v3_model) -> None:
    """Test that providing V3L model with version='v3' raises."""
    v3l_model = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
    with pytest.raises(CrossVersionValidationError, match="Version 'v3' requires MappingPackageV3"):
        validate_mapping_package(v3l_model, version="v3")


# --- validate_mapping_package: path validation ---


def test_validate_mapping_package_raises_on_nonexistent_folder_path(tmp_path: Path) -> None:
    """Test that validating a non-existent folder path raises."""
    nonexistent_path = tmp_path / "does_not_exist"
    with pytest.raises(Exception):
        validate_mapping_package(nonexistent_path)


def test_validate_mapping_package_raises_on_nonexistent_archive_path(tmp_path: Path) -> None:
    """Test that validating a non-existent archive path raises."""
    nonexistent_archive = tmp_path / "does_not_exist.zip"
    with pytest.raises(Exception):
        validate_mapping_package(nonexistent_archive)


def test_validate_mapping_package_raises_on_file_when_folder_expected(tmp_path: Path) -> None:
    """Test that passing a file path when folder is expected raises."""
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
            return_value=Version.V2,
        ),
    ):
        with pytest.raises(Exception):  # validate_folder_path should raise
            validate_mapping_package(file_path)


def test_validate_mapping_package_folder_path_validation_is_called(tmp_path: Path) -> None:
    """Test that folder path validation is called for directory paths."""
    folder_path = tmp_path / "package"
    folder_path.mkdir()

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.MPValidationStepABC.validate_path_exists",
        ) as mock_validate_path,
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.MPValidationStepABC.validate_folder_path",
        ) as mock_validate_folder,
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
            return_value=Version.V2,
        ),
        patch(
            "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder",
            return_value=True,
        ),
    ):
        validate_mapping_package(folder_path)
        mock_validate_path.assert_called_once()
        mock_validate_folder.assert_called_once()


def test_validate_mapping_package_archive_path_validation_is_called(tmp_path: Path) -> None:
    """Test that archive path validation is called for file paths."""
    archive_path = tmp_path / "package.zip"
    archive_path.write_text("dummy")

    with (
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.MPValidationStepABC.validate_path_exists",
        ) as mock_validate_path,
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.MPValidationStepABC.validate_archive_path",
        ) as mock_validate_archive,
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.ArchiveExtractor.extract",
            return_value=tmp_path / "extracted",
        ),
        patch(
            "mapping_suite_sdk.tools.services.validate_mapping_package.detect_mapping_package_version",
            return_value=Version.V2,
        ),
        patch(
            "mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2.validate_mapping_package_v2_from_folder",
            return_value=True,
        ),
    ):
        validate_mapping_package(archive_path)
        mock_validate_path.assert_called_once()
        mock_validate_archive.assert_called_once()
