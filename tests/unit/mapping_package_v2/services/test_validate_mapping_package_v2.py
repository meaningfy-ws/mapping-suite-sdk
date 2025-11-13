import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_validator import MPHashValidationException, \
    MappingPackageV2Validator
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2 import validate_mapping_package_v2, \
    validate_mapping_package_v2_from_archive, validate_mapping_package_v2_from_folder, \
    validate_bulk_mapping_packages_v2_from_folder, validate_bulk_mapping_packages_v2_from_github
from tests.test_helpers import get_random_string, setup_temporary_test_git_repository


def test_validate_mapping_package_v2_runs_with_success(dummy_mapping_package_v2_model: MappingPackageV2):
    is_valid: bool = validate_mapping_package_v2(mapping_package=dummy_mapping_package_v2_model)

    assert is_valid == True

    is_valid: bool = validate_mapping_package_v2(mapping_package=dummy_mapping_package_v2_model,
                                                 mp_validator=MappingPackageV2Validator())

    assert is_valid == True


def test_validate_mapping_package_v2_fails_on_bad_package(dummy_mapping_package_v2_model: MappingPackageV2):
    random_string: str = get_random_string()
    assert random_string != dummy_mapping_package_v2_model.metadata.signature
    dummy_mapping_package_v2_model.metadata.signature = random_string
    with pytest.raises(MPHashValidationException):
        validate_mapping_package_v2(mapping_package=dummy_mapping_package_v2_model)


def test_validate_mapping_package_v2_from_archive_runs_with_success(dummy_mapping_package_v2_archive_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path: Path = Path(tmpdir)
        tmpdir_archive_path: Path = tmpdir_path / dummy_mapping_package_v2_archive_path.name

        shutil.copy(dummy_mapping_package_v2_archive_path, tmpdir_archive_path)

        is_valid: bool = validate_mapping_package_v2_from_archive(tmpdir_archive_path)

    assert is_valid


def test_validate_mapping_package_v2_from_archive_fails_on_bad_archive_path():
    wrong_path: Path = Path(get_random_string())
    assert not wrong_path.is_file()
    assert not wrong_path.is_dir()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v2_from_archive(wrong_path)


def test_validate_mapping_package_v2_from_folder_runs_with_success(dummy_mapping_package_v2_path: Path):
    is_valid: bool = validate_mapping_package_v2_from_folder(dummy_mapping_package_v2_path)

    assert is_valid == True


def test_validate_mapping_package_v2_from_folder_fails_on_bad_folder_path():
    wrong_path: Path = Path(get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v2_from_folder(wrong_path)


def test_validate_mapping_package_v2_from_folder_fails_on_non_directory():
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_mapping_package_v2_from_folder(file_path)
    temp_file.close()


def test_validate_bulk_mapping_packages_v2_from_folder_runs_with_success(dummy_mapping_package_v2_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "packageV2"
        shutil.copytree(dummy_mapping_package_v2_path, package_dir)

        validate_bulk_mapping_packages_v2_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v2_from_folder_fails_on_bad_folder_path():
    wrong_path: Path = Path(get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_bulk_mapping_packages_v2_from_folder(wrong_path)


def test_validate_bulk_mapping_packages_v2_from_folder_fails_on_non_directory():
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_bulk_mapping_packages_v2_from_folder(file_path)


def test_validate_bulk_mapping_packages_v2_from_folder_continues_on_package_failure(
        dummy_mapping_package_v2_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        valid_package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v2_path, valid_package_dir)

        invalid_package_dir = tmpdir_path / "package2"
        shutil.copytree(dummy_mapping_package_v2_path, invalid_package_dir)

        metadata_file = invalid_package_dir / "metadata.json"
        metadata_file.write_text("invalid json")

        validate_bulk_mapping_packages_v2_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v2_from_github_runs_with_success(dummy_github_project_path: Path,
                                                                         dummy_get_all_packages_pattern: str):
    with setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v2_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern)


def test_validate_bulk_mapping_packages_v2_from_github_fails_on_empty_repo_url():
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v2_from_github(
            github_repository_url="",
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v2_from_github_fails_on_bad_url(dummy_invalid_github_repo_url: str):
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v2_from_github(
            github_repository_url=dummy_invalid_github_repo_url,
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v2_from_github_fails_on_empty_pattern():
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v2_from_github(
            github_repository_url="https://github.com/test/repo",
            packages_path_pattern="")


def test_validate_bulk_mapping_packages_v2_from_github_continues_on_package_failure(dummy_github_project_path: Path,
                                                                                    dummy_get_all_packages_pattern: str):
    with setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v2_from_github(
            github_repository_url=repo_path,
            # Getting bad packages
            packages_path_pattern=dummy_get_all_packages_pattern)
