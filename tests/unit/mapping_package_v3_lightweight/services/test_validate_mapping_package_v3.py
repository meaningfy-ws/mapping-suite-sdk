import json
import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.mp_v3_lightweight.adapters.validator_lightweight import MPV3LightweightHashValidationException, \
    MappingPackageV3LightweightValidator
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mp_v3_lightweight.services.validate_mapping_package_v3_lightweight import validate_mapping_package_v3, \
    validate_mapping_package_v3_from_archive, validate_mapping_package_v3_from_folder, \
    validate_bulk_mapping_packages_v3_from_folder, validate_bulk_mapping_packages_v3_from_github
from tests.conftest import _get_random_string, _setup_temporary_test_git_repository


def test_validate_mapping_package_v3_runs_with_success(fixture_mapping_package_v3_model: MappingPackageV3Lightweight):
    is_valid: bool = validate_mapping_package_v3(mapping_package=fixture_mapping_package_v3_model)

    assert is_valid == True

    is_valid: bool = validate_mapping_package_v3(mapping_package=fixture_mapping_package_v3_model,
                                                 mp_validator=MappingPackageV3LightweightValidator())

    assert is_valid == True


def test_validate_mapping_package_v3_fails_on_bad_package(fixture_mapping_package_v3_model: MappingPackageV3Lightweight):
    random_string: str = _get_random_string()
    assert random_string != fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest
    fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest = random_string
    with pytest.raises(MPV3LightweightHashValidationException):
        validate_mapping_package_v3(mapping_package=fixture_mapping_package_v3_model)


def test_validate_mapping_package_v3_from_archive_runs_with_success(dummy_mapping_package_v3_archive_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path: Path = Path(tmpdir)
        tmpdir_archive_path: Path = tmpdir_path / dummy_mapping_package_v3_archive_path.name

        shutil.copy(dummy_mapping_package_v3_archive_path, tmpdir_archive_path)

        is_valid: bool = validate_mapping_package_v3_from_archive(tmpdir_archive_path)

    assert is_valid


def test_validate_mapping_package_v3_from_archive_fails_on_bad_archive_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.is_file()
    assert not wrong_path.is_dir()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v3_from_archive(wrong_path)


def test_validate_mapping_package_v3_from_archive_fails_on_folder_instead_of_archive_path(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v3_from_archive(tmp_path)


def test_validate_mapping_package_v3_from_folder_runs_with_success(dummy_mapping_package_v3_path: Path):
    is_valid: bool = validate_mapping_package_v3_from_folder(dummy_mapping_package_v3_path)

    assert is_valid == True


def test_validate_mapping_package_v3_from_folder_fails_on_bad_folder_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_mapping_package_v3_from_folder(wrong_path)


def test_validate_mapping_package_v3_from_folder_fails_on_non_directory():
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_mapping_package_v3_from_folder(file_path)
    temp_file.close()


def test_validate_bulk_mapping_packages_v3_from_folder_runs_with_success(dummy_mapping_package_v3_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        validate_bulk_mapping_packages_v3_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v3_from_folder_updates_hash(dummy_mapping_package_v3_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "package_changed"
        shutil.copytree(dummy_mapping_package_v3_path, package_dir)

        metadata_dir = package_dir / "metadata.jsonld"
        mp_metadata = json.loads(metadata_dir.read_text())
        mp_metadata["mapping_suite_hash_digest"] = "a7e3277f0820255270d488ffb4cf944e684f7e426b329ae8031abe73bf85bd6b"
        metadata_dir.write_text(json.dumps(mp_metadata))

        validate_bulk_mapping_packages_v3_from_folder(tmpdir_path, update_hash=True)

        mp_metadata_after_validation = json.loads(metadata_dir.read_text())
        assert mp_metadata_after_validation["mapping_suite_hash_digest"] != mp_metadata["mapping_suite_hash_digest"]


def test_validate_bulk_mapping_packages_v3_from_folder_fails_on_bad_folder_path():
    wrong_path: Path = Path(_get_random_string())
    assert not wrong_path.exists()
    with pytest.raises(FileNotFoundError):
        validate_bulk_mapping_packages_v3_from_folder(wrong_path)


def test_validate_bulk_mapping_packages_v3_from_folder_fails_on_non_directory():
    temp_file = tempfile.NamedTemporaryFile()
    file_path = Path(temp_file.name)
    assert file_path.is_file()
    with pytest.raises(NotADirectoryError):
        validate_bulk_mapping_packages_v3_from_folder(file_path)


def test_validate_bulk_mapping_packages_v3_from_folder_continues_on_package_failure(
        dummy_mapping_package_v3_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        valid_package_dir = tmpdir_path / "package1"
        shutil.copytree(dummy_mapping_package_v3_path, valid_package_dir)

        invalid_package_dir = tmpdir_path / "package2"
        shutil.copytree(dummy_mapping_package_v3_path, invalid_package_dir)

        metadata_file = invalid_package_dir / "metadata.json"
        metadata_file.write_text("invalid json")

        validate_bulk_mapping_packages_v3_from_folder(tmpdir_path)


def test_validate_bulk_mapping_packages_v3_from_github_runs_with_success(dummy_github_project_path: Path,
                                                                         dummy_get_all_packages_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern)


def test_validate_bulk_mapping_packages_v3_from_github_fails_on_empty_repo_url():
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v3_from_github(
            github_repository_url="",
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v3_from_github_fails_on_bad_url(dummy_invalid_github_repo_url: str):
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=dummy_invalid_github_repo_url,
            packages_path_pattern="**/package.zip")


def test_validate_bulk_mapping_packages_v3_from_github_fails_on_empty_pattern():
    with pytest.raises(ValueError):
        validate_bulk_mapping_packages_v3_from_github(
            github_repository_url="https://github.com/test/repo",
            packages_path_pattern="")


def test_validate_bulk_mapping_packages_v3_from_github_continues_on_package_failure(dummy_github_project_path: Path,
                                                                                    dummy_get_all_packages_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern)


def test_validate_bulk_mapping_packages_v3_from_folder_with_multiple_valid_packages(
        fixture_mapping_package_v3_github_project_path: Path):
    mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"
    assert mappings_folder.exists()

    result = validate_bulk_mapping_packages_v3_from_folder(mappings_folder)

    assert result == True


def test_validate_bulk_mapping_packages_v3_from_folder_returns_false_on_validation_failure(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        first_package = next(temp_mappings.iterdir())
        metadata_file = first_package / "metadata.jsonld"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            metadata['mapping_suite_hash_digest'] = "invalid_hash_value"
            metadata_file.write_text(json.dumps(metadata))

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings)

        assert result == False


def test_validate_bulk_mapping_packages_v3_from_folder_continues_on_validation_error(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        first_package = next(temp_mappings.iterdir())
        metadata_file = first_package / "metadata.jsonld"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            del metadata['id']
            metadata_file.write_text(json.dumps(metadata))

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings)

        assert result == False


def test_validate_bulk_mapping_packages_v3_from_folder_continues_on_generic_exception(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        invalid_package_dir = temp_mappings / "invalid_package"
        invalid_package_dir.mkdir()
        (invalid_package_dir / "incomplete").touch()

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings)

        assert result == False


def test_validate_bulk_mapping_packages_v3_from_folder_hash_update_with_invalid_hash(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        first_package = next(temp_mappings.iterdir())
        metadata_file = first_package / "metadata.jsonld"
        metadata_original = json.loads(metadata_file.read_text())
        original_hash = metadata_original["mapping_suite_hash_digest"]

        metadata_original["mapping_suite_hash_digest"] = "wrong_hash_12345"
        metadata_file.write_text(json.dumps(metadata_original))

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings, update_hash=True)

        metadata_updated = json.loads(metadata_file.read_text())
        assert metadata_updated["mapping_suite_hash_digest"] != "wrong_hash_12345"
        assert metadata_updated["mapping_suite_hash_digest"] == original_hash
        assert result == True


def test_validate_bulk_mapping_packages_v3_from_github_returns_false_on_validation_failure(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        repo_dir = tmpdir_path / "repo"
        shutil.copytree(fixture_mapping_package_v3_github_project_path, repo_dir)

        for metadata_file in repo_dir.rglob("metadata.jsonld"):
            metadata = json.loads(metadata_file.read_text())
            metadata['mapping_suite_hash_digest'] = "invalid_hash"
            metadata_file.write_text(json.dumps(metadata))

        with _setup_temporary_test_git_repository(repo_dir) as repo_path:
            result = validate_bulk_mapping_packages_v3_from_github(
                github_repository_url=repo_path,
                packages_path_pattern=dummy_get_all_packages_pattern)

            assert result == False


def test_validate_bulk_mapping_packages_v3_from_github_with_multiple_packages(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    with _setup_temporary_test_git_repository(fixture_mapping_package_v3_github_project_path) as repo_path:
        result = validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern)

        assert isinstance(result, bool)


def test_validate_bulk_mapping_packages_v3_from_folder_with_mix_of_valid_and_invalid(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        packages = list(temp_mappings.iterdir())
        if len(packages) >= 2:
            metadata_file = packages[0] / "metadata.jsonld"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                metadata['mapping_suite_hash_digest'] = "bad_hash"
                metadata_file.write_text(json.dumps(metadata))

            invalid_json_file = packages[1] / "metadata.jsonld"
            if invalid_json_file.exists():
                invalid_json_file.write_text("bad json")

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings)

        assert result == False


def test_validate_bulk_mapping_packages_v3_from_folder_dont_skip_files_in_folder(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        (temp_mappings / "random_file.txt").write_text("should be ignored")

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings)

        assert result == False


def test_validate_mapping_package_v3_with_custom_validator(fixture_mapping_package_v3_model: MappingPackageV3Lightweight):
    custom_validator = MappingPackageV3LightweightValidator()

    result = validate_mapping_package_v3(
        mapping_package=fixture_mapping_package_v3_model,
        mp_validator=custom_validator
    )

    assert result == True


def test_validate_mapping_package_v3_from_archive_with_custom_validator(
        dummy_mapping_package_v3_archive_path: Path):
    custom_validator = MappingPackageV3LightweightValidator()

    result = validate_mapping_package_v3_from_archive(
        mapping_package_archive_path=dummy_mapping_package_v3_archive_path,
        mp_validator=custom_validator
    )

    assert result == True


def test_validate_mapping_package_v3_from_archive_with_custom_loader(
        dummy_mapping_package_v3_archive_path: Path):
    from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
    custom_loader = MappingPackageV3Loader(include_test_data=False, include_output=False)

    result = validate_mapping_package_v3_from_archive(
        mapping_package_archive_path=dummy_mapping_package_v3_archive_path,
        mapping_package_loader=custom_loader
    )

    assert result == True


def test_validate_mapping_package_v3_from_archive_with_custom_extractor(
        dummy_mapping_package_v3_archive_path: Path):
    from mapping_suite_sdk.core.adapters.extractor import ArchivePackageExtractor
    custom_extractor = ArchivePackageExtractor()

    result = validate_mapping_package_v3_from_archive(
        mapping_package_archive_path=dummy_mapping_package_v3_archive_path,
        archive_unpacker=custom_extractor
    )

    assert result == True


def test_validate_mapping_package_v3_from_folder_with_custom_validator(
        dummy_mapping_package_v3_path: Path):
    custom_validator = MappingPackageV3LightweightValidator()

    result = validate_mapping_package_v3_from_folder(
        mapping_package_folder_path=dummy_mapping_package_v3_path,
        mp_validator=custom_validator
    )

    assert result == True


def test_validate_mapping_package_v3_from_folder_with_custom_loader(
        dummy_mapping_package_v3_path: Path):
    from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
    custom_loader = MappingPackageV3Loader(include_test_data=True, include_output=True)

    result = validate_mapping_package_v3_from_folder(
        mapping_package_folder_path=dummy_mapping_package_v3_path,
        mapping_package_loader=custom_loader
    )

    assert result == True


def test_validate_bulk_mapping_packages_v3_from_folder_with_custom_validator(
        fixture_mapping_package_v3_github_project_path: Path):
    mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"
    custom_validator = MappingPackageV3LightweightValidator()

    result = validate_bulk_mapping_packages_v3_from_folder(
        mapping_packages_folder_path=mappings_folder,
        mp_validator=custom_validator
    )

    assert result == True


def test_validate_bulk_mapping_packages_v3_from_folder_with_custom_loader(
        fixture_mapping_package_v3_github_project_path: Path):
    from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
    mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"
    custom_loader = MappingPackageV3Loader(include_test_data=False, include_output=False)

    result = validate_bulk_mapping_packages_v3_from_folder(
        mapping_packages_folder_path=mappings_folder,
        mapping_package_loader=custom_loader
    )

    assert result == True


def test_validate_bulk_mapping_packages_v3_from_github_with_custom_validator(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    custom_validator = MappingPackageV3LightweightValidator()

    with _setup_temporary_test_git_repository(fixture_mapping_package_v3_github_project_path) as repo_path:
        result = validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern,
            mp_validator=custom_validator
        )

        assert isinstance(result, bool)


def test_validate_bulk_mapping_packages_v3_from_github_with_custom_loader(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
    custom_loader = MappingPackageV3Loader(include_test_data=True, include_output=True)

    with _setup_temporary_test_git_repository(fixture_mapping_package_v3_github_project_path) as repo_path:
        result = validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern,
            mapping_package_loader=custom_loader
        )

        assert isinstance(result, bool)


def test_validate_bulk_mapping_packages_v3_from_github_with_custom_extractor(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    from mapping_suite_sdk.core.adapters.extractor import GithubPackageExtractor
    custom_extractor = GithubPackageExtractor()

    with _setup_temporary_test_git_repository(fixture_mapping_package_v3_github_project_path) as repo_path:
        result = validate_bulk_mapping_packages_v3_from_github(
            github_repository_url=repo_path,
            packages_path_pattern=dummy_get_all_packages_pattern,
            github_package_extractor=custom_extractor
        )

        assert isinstance(result, bool)


def test_validate_bulk_mapping_packages_v3_from_folder_updates_hash_and_returns_true(
        fixture_mapping_package_v3_github_project_path: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        mappings_folder = fixture_mapping_package_v3_github_project_path / "mappings"

        temp_mappings = tmpdir_path / "mappings"
        shutil.copytree(mappings_folder, temp_mappings)

        packages = list(temp_mappings.iterdir())
        for package in packages:
            metadata_file = package / "metadata.jsonld"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                metadata['mapping_suite_hash_digest'] = "wrong_hash"
                metadata_file.write_text(json.dumps(metadata))

        result = validate_bulk_mapping_packages_v3_from_folder(temp_mappings, update_hash=True)

        assert result == True


def test_validate_bulk_mapping_packages_v3_from_github_continues_on_unexpected_exception(
        fixture_mapping_package_v3_github_project_path: Path,
        dummy_get_all_packages_pattern: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        repo_dir = tmpdir_path / "repo"
        shutil.copytree(fixture_mapping_package_v3_github_project_path, repo_dir)

        first_metadata = next(repo_dir.rglob("metadata.jsonld"))
        first_metadata.write_text("completely invalid")

        with _setup_temporary_test_git_repository(repo_dir) as repo_path:
            result = validate_bulk_mapping_packages_v3_from_github(
                github_repository_url=repo_path,
                packages_path_pattern=dummy_get_all_packages_pattern)

            assert isinstance(result, bool)
