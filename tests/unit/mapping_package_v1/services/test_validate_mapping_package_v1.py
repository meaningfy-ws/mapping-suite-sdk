import json
import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk import MappingPackageV1, validate_mapping_package_v1, MappingPackageV1Validator, \
    validate_mapping_package_v1_from_archive, validate_mapping_package_v1_from_folder, \
    validate_bulk_mapping_packages_v1_from_folder, validate_bulk_mapping_packages_v1_from_github
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_validator import MPHashValidationException
from tests.conftest import _get_random_string, _setup_temporary_test_git_repository


def test_validate_mapping_package_v1_runs_with_success(dummy_mapping_package_v1_model: MappingPackageV1):
    is_valid: bool = validate_mapping_package_v1(mapping_package=dummy_mapping_package_v1_model)

    assert is_valid == True

    is_valid: bool = validate_mapping_package_v1(mapping_package=dummy_mapping_package_v1_model,
                                                 mp_validator=MappingPackageV1Validator())

    assert is_valid == True


def test_validate_mapping_package_v1_fails_on_bad_package(dummy_mapping_package_v1_model: MappingPackageV1):
    random_string: str = _get_random_string()
    assert random_string != dummy_mapping_package_v1_model.metadata.signature
    dummy_mapping_package_v1_model.metadata.signature = random_string
    with pytest.raises(MPHashValidationException):
        validate_mapping_package_v1(mapping_package=dummy_mapping_package_v1_model)


def test_validate_mapping_package_v1_from_archive_runs_with_success(dummy_mapping_package_v1_archive_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path: Path = Path(tmpdir)
        tmpdir_archive_path: Path = tmpdir_path / dummy_mapping_package_v1_archive_path.name

        shutil.copy(dummy_mapping_package_v1_archive_path, tmpdir_archive_path)

        is_valid: bool = validate_mapping_package_v1_from_archive(tmpdir_archive_path)

    assert is_valid


def test_validate_mapping_package_v1_from_archive_fails_on_bad_archive_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.is_file()
    assert not wrong_path.is_dir()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v1_from_archive(wrong_path)


def test_validate_mapping_package_v1_from_archive_fails_on_folder_instead_of_archive_path(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v1_from_archive(tmp_path)


def test_validate_mapping_package_v1_from_folder_runs_with_success(dummy_mapping_package_v1_path: Path):
    is_valid: bool = validate_mapping_package_v1_from_folder(dummy_mapping_package_v1_path)

    assert is_valid == True


def test_validate_mapping_package_v1_from_folder_fails_on_bad_folder_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v1_from_folder(wrong_path)


def test_validate_mapping_package_v1_from_folder_fails_on_non_directory():
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_mapping_package_v1_from_folder(file_path)
    temp_file.close()


def test_validate_bulk_mapping_packages_v1_from_folder_runs_with_success(dummy_mapping_package_v1_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v1_path, package_dir)

        validate_bulk_mapping_packages_v1_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v1_from_folder_updates_hash(dummy_mapping_package_v1_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package_F22_changed"
        shutil.copytree(dummy_mapping_package_v1_path, package_dir)

        metadata_dir = package_dir / "package_F22_changed" / "metadata.json"
        mp_metadata = json.loads(metadata_dir.read_text())
        # Wrong signature
        mp_metadata["mapping_suite_hash_digest"] = "a7e3277f0820255270d488ffb4cf944e684f7e426b329ae8031abe73bf85bd6b"
        metadata_dir.write_text(json.dumps(mp_metadata))

        validate_bulk_mapping_packages_v1_from_folder(tmpdir_path, update_hash=True)

        mp_metadata_after_validation = json.loads(metadata_dir.read_text())
        assert mp_metadata_after_validation["mapping_suite_hash_digest"] != mp_metadata["mapping_suite_hash_digest"]


def test_validate_bulk_mapping_packages_v1_from_folder_fails_on_bad_folder_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_bulk_mapping_packages_v1_from_folder(wrong_path)


def test_validate_bulk_mapping_packages_v1_from_folder_fails_on_non_directory():
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_bulk_mapping_packages_v1_from_folder(file_path)


def test_validate_bulk_mapping_packages_v1_from_folder_continues_on_package_failure(
        dummy_mapping_package_v1_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        valid_package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v1_path, valid_package_dir)

        invalid_package_dir = tmpdir_path / "package2"
        shutil.copytree(dummy_mapping_package_v1_path, invalid_package_dir)

        metadata_file = invalid_package_dir / "metadata.json"
        metadata_file.write_text("invalid json")

        validate_bulk_mapping_packages_v1_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v1_from_github_runs_with_success(dummy_github_project_path: Path,
                                                                         dummy_get_all_packages_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v1_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern)


def test_validate_bulk_mapping_packages_v1_from_github_fails_on_empty_repo_url():
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v1_from_github(
            github_repository_url="",
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v1_from_github_fails_on_bad_url(dummy_invalid_github_repo_url: str):
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v1_from_github(
            github_repository_url=dummy_invalid_github_repo_url,
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v1_from_github_fails_on_empty_pattern():
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v1_from_github(
            github_repository_url="https://github.com/test/repo",
            packages_path_pattern="")


def test_validate_bulk_mapping_packages_v1_from_github_continues_on_package_failure(dummy_github_project_path: Path,
                                                                                    dummy_get_all_packages_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v1_from_github(
            github_repository_url=repo_path,
            # Getting bad packages
            packages_path_pattern=dummy_get_all_packages_pattern)
