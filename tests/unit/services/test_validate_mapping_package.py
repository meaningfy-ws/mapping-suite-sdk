import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.adapters.validator import MappingPackageValidator, MPHashValidationException
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.services.validate_mapping_package import validate_mapping_package, \
    validate_mapping_package_from_archive
from tests import TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH
from tests.conftest import _get_random_string


def test_validate_mapping_package_runs_with_success(dummy_mapping_package_model: MappingPackage,
                                                    dummy_mapping_package_validator: MappingPackageValidator):
    is_valid: bool = validate_mapping_package(mapping_package=dummy_mapping_package_model)

    assert is_valid == True

    is_valid: bool = validate_mapping_package(mapping_package=dummy_mapping_package_model,
                                              mp_validator=dummy_mapping_package_validator)

    assert is_valid == True


def test_validate_mapping_package_fails_on_bad_package(dummy_mapping_package_model: MappingPackage,
                                                       dummy_mapping_package_validator: MappingPackageValidator):
    random_string: str = _get_random_string()
    assert random_string != dummy_mapping_package_model.metadata.signature
    dummy_mapping_package_model.metadata.signature = random_string
    with pytest.raises(MPHashValidationException):
        validate_mapping_package(mapping_package=dummy_mapping_package_model)


def test_validate_mapping_package_from_archive_runs_with_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path: Path = Path(tmpdir)
        tmpdir_archive_path: Path = tmpdir_path / TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH.name

        shutil.copy(TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH, tmpdir_archive_path)

        is_valid: bool = validate_mapping_package_from_archive(tmpdir_archive_path)

    assert is_valid


def test_validate_mapping_package_from_archive_fails_on_bad_archive_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.is_file()
    assert not wrong_path.is_dir()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_from_archive(wrong_path)
