import json
import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.core.adapters.validator_abc import MPValidationException
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader import MappingPackageV3LightweightLoader
from mapping_suite_sdk.mapping_package_v3.services.validate_mapping_package_v3_lightweight import (
    validate_mapping_package_v3_lightweight,
    validate_mapping_package_v3_lightweight_from_archive,
    validate_mapping_package_v3_lightweight_from_folder,
    validate_bulk_mapping_packages_v3_lightweight_from_folder,
    validate_bulk_mapping_packages_v3_lightweight_from_github
)
from tests.test_helpers import get_random_string, setup_temporary_test_git_repository


def test_validate_mapping_package_v3_lightweight_runs_with_success(
        dummy_mapping_package_v3_path: Path):
    """Test that lightweight validation succeeds with correct hash."""
    from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import \
        load_mapping_package_v3_from_folder

    lightweight_package = load_mapping_package_v3_from_folder(dummy_mapping_package_v3_path)
    # Set correct hash
    hasher = MappingPackageV3Hasher(lightweight_package)  # type: ignore[arg-type]
    lightweight_package.metadata.mapping_suite_hash_digest = hasher.hash()

    is_valid = validate_mapping_package_v3_lightweight(mapping_package=lightweight_package)
    assert is_valid is True


def test_validate_mapping_package_v3_lightweight_fails_on_bad_hash(
        dummy_mapping_package_v3_path: Path):
    """Test that lightweight validation fails with incorrect hash."""
    from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight import \
        load_mapping_package_v3_from_folder

    lightweight_package = load_mapping_package_v3_from_folder(dummy_mapping_package_v3_path)
    random_string = get_random_string()
    lightweight_package.metadata.mapping_suite_hash_digest = random_string

    with pytest.raises(MPValidationException):
        validate_mapping_package_v3_lightweight(mapping_package=lightweight_package)


def test_validate_mapping_package_v3_lightweight_from_archive_runs_with_success(
        dummy_mapping_package_v3_archive_path: Path):
    """Test lightweight validation from archive succeeds."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tmpdir_archive_path = tmpdir_path / dummy_mapping_package_v3_archive_path.name
        shutil.copy(dummy_mapping_package_v3_archive_path, tmpdir_archive_path)

        is_valid = validate_mapping_package_v3_lightweight_from_archive(tmpdir_archive_path)
        assert is_valid is True


def test_validate_mapping_package_v3_lightweight_from_archive_fails_on_bad_archive_path():
    """Test lightweight validation from archive fails on non-existent path."""
    wrong_path = Path(get_random_string())
    assert not wrong_path.is_file()
    assert not wrong_path.is_dir()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v3_lightweight_from_archive(wrong_path)


def test_validate_mapping_package_v3_lightweight_from_archive_fails_on_folder_instead_of_archive(
        tmp_path: Path):
    """Test lightweight validation from archive fails when path is a folder."""
    with pytest.raises(ValueError) as exc_info:
        validate_mapping_package_v3_lightweight_from_archive(tmp_path)

    assert "Cannot process validate package from archive" in str(exc_info.value)
    assert "Path is not a file" in str(exc_info.value)


def test_validate_mapping_package_v3_lightweight_from_folder_runs_with_success(
        dummy_mapping_package_v3_path: Path):
    """Test lightweight validation from folder succeeds."""
    is_valid = validate_mapping_package_v3_lightweight_from_folder(dummy_mapping_package_v3_path)
    assert is_valid is True


def test_validate_mapping_package_v3_lightweight_from_folder_fails_on_bad_folder_path():
    """Test lightweight validation from folder fails on non-existent path."""
    wrong_path = Path(get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v3_lightweight_from_folder(wrong_path)


def test_validate_mapping_package_v3_lightweight_from_folder_fails_on_non_directory():
    """Test lightweight validation from folder fails when path is a file."""
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_mapping_package_v3_lightweight_from_folder(file_path)
    temp_file.close()


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_runs_with_success(
        dummy_mapping_package_v3_path: Path):
    """Test bulk lightweight validation from folder succeeds."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        validate_bulk_mapping_packages_v3_lightweight_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_updates_hash(
        dummy_mapping_package_v3_path: Path):
    """Test bulk lightweight validation updates hash when update_hash=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package_changed"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        metadata_file = package_dir / "metadata.jsonld"
        mp_metadata = json.loads(metadata_file.read_text())
        mp_metadata["mapping_suite_hash_digest"] = "a7e3277f0820255270d488ffb4cf944e684f7e426b329ae8031abe73bf85bd6b"
        metadata_file.write_text(json.dumps(mp_metadata))

        validate_bulk_mapping_packages_v3_lightweight_from_folder(tmpdir_path, update_hash=True)

        mp_metadata_after_validation = json.loads(metadata_file.read_text())
        assert mp_metadata_after_validation["mapping_suite_hash_digest"] != mp_metadata["mapping_suite_hash_digest"]


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_fails_on_bad_folder_path():
    """Test bulk lightweight validation fails on non-existent path."""
    wrong_path = Path(get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_bulk_mapping_packages_v3_lightweight_from_folder(wrong_path)


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_fails_on_non_directory():
    """Test bulk lightweight validation fails when path is a file."""
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_bulk_mapping_packages_v3_lightweight_from_folder(file_path)
    temp_file.close()


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_continues_on_package_failure(
        dummy_mapping_package_v3_path: Path):
    """Test bulk lightweight validation continues when a package fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        valid_package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, valid_package_dir)

        invalid_package_dir = tmpdir_path / "package2"
        shutil.copytree(dummy_mapping_package_v3_path, invalid_package_dir)

        metadata_file = invalid_package_dir / "metadata.jsonld"
        metadata_file.write_text("invalid json")

        validate_bulk_mapping_packages_v3_lightweight_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v3_lightweight_from_github_runs_with_success(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    """Test bulk lightweight validation from GitHub succeeds."""
    with setup_temporary_test_git_repository(fixture_mapping_package_v3_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v3_lightweight_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern)


def test_validate_bulk_mapping_packages_v3_lightweight_from_github_fails_on_empty_repo_url():
    """Test bulk lightweight validation from GitHub fails on empty URL."""
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v3_lightweight_from_github(
            github_repository_url="",
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v3_lightweight_from_github_fails_on_empty_pattern():
    """Test bulk lightweight validation from GitHub fails on empty pattern."""
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v3_lightweight_from_github(
            github_repository_url="https://github.com/test/repo",
            packages_path_pattern="")


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_returns_false_on_validation_failure(
        dummy_mapping_package_v3_path: Path):
    """Test bulk lightweight validation returns False when validation fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        metadata_file = package_dir / "metadata.jsonld"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            metadata['mapping_suite_hash_digest'] = "invalid_hash_value"
            metadata_file.write_text(json.dumps(metadata))

        result = validate_bulk_mapping_packages_v3_lightweight_from_folder(tmpdir_path)
        assert result is False


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_skips_non_directory_files(
        dummy_mapping_package_v3_path: Path):
    """Test bulk lightweight validation skips non-directory files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        (tmpdir_path / "random_file.txt").write_text("should be ignored")

        result = validate_bulk_mapping_packages_v3_lightweight_from_folder(tmpdir_path)
        assert result is True


def test_validate_mapping_package_v3_lightweight_from_archive_with_custom_loader(
        dummy_mapping_package_v3_archive_path: Path):
    """Test lightweight validation from archive with custom loader."""
    custom_loader = MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)

    result = validate_mapping_package_v3_lightweight_from_archive(
        mapping_package_archive_path=dummy_mapping_package_v3_archive_path,
        mapping_package_loader=custom_loader)

    assert result is True


def test_validate_mapping_package_v3_lightweight_from_folder_with_custom_loader(
        dummy_mapping_package_v3_path: Path):
    """Test lightweight validation from folder with custom loader."""
    custom_loader = MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)

    result = validate_mapping_package_v3_lightweight_from_folder(
        mapping_package_folder_path=dummy_mapping_package_v3_path,
        mapping_package_loader=custom_loader)

    assert result is True


def test_validate_bulk_mapping_packages_v3_lightweight_from_folder_with_custom_loader(
        dummy_mapping_package_v3_path: Path):
    """Test bulk lightweight validation from folder with custom loader."""
    custom_loader = MappingPackageV3LightweightLoader(include_test_data=False, include_output=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        result = validate_bulk_mapping_packages_v3_lightweight_from_folder(
            mapping_packages_folder_path=tmpdir_path,
            mapping_package_loader=custom_loader)

        assert result is True


def test_validate_bulk_mapping_packages_v3_lightweight_from_github_with_custom_loader(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    """Test bulk lightweight validation from GitHub with custom loader."""
    custom_loader = MappingPackageV3LightweightLoader(include_test_data=True, include_output=True)

    with setup_temporary_test_git_repository(fixture_mapping_package_v3_github_project_path) as repo_path:
        result = validate_bulk_mapping_packages_v3_lightweight_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern,
            mapping_package_loader=custom_loader)

        assert isinstance(result, bool)
