import shutil
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.core.adapters.extractor import (
    ExtractorABC,
    ArchiveExtractor,
    GitHubExtractor
)
from tests.test_helpers import compare_directories, setup_temporary_test_git_repository


def test_archive_extractor_extract_temporary_successful(dummy_mapping_package_path: Path) -> None:
    with ArchiveExtractor().extract_temporary(dummy_mapping_package_path) as extracted_path:
        assert extracted_path.exists()
        assert extracted_path.is_dir()


def test_archive_extractor_cleanup_after_context(dummy_mapping_package_path: Path) -> None:
    with ArchiveExtractor().extract_temporary(dummy_mapping_package_path) as path:
        extracted_path = path
        assert extracted_path.exists()

    assert not extracted_path.exists()


def test_archive_extractor_extract_to_destination(dummy_mapping_package_path: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        dest_path = temp_dir_path / "destination"
        dest_path.mkdir()

        result_path = ArchiveExtractor().extract(dummy_mapping_package_path, dest_path)

        assert result_path.exists()
        assert result_path.is_dir()
        assert result_path.parent == dest_path


def test_archive_extractor_nonexistent_file() -> None:
    with pytest.raises(FileNotFoundError):
        with ArchiveExtractor().extract_temporary(Path("nonexistent.zip")):
            ...


def test_archive_extractor_invalid_file_path() -> None:
    with pytest.raises(ValueError):
        with ArchiveExtractor().extract_temporary(Path(__file__)):
            ...


def test_archive_extractor_corrupted_file(dummy_corrupted_mapping_package_path: Path) -> None:
    with pytest.raises(ValueError):
        with ArchiveExtractor().extract_temporary(dummy_corrupted_mapping_package_path):
            ...


def test_archive_extractor_pack_directory_generates_same_output(
        dummy_mapping_package_extracted_path: Path,
        dummy_mapping_package_path: Path
) -> None:
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_directory_path = Path(temp_directory)

        archived_path = ArchiveExtractor().pack_directory(
            dummy_mapping_package_extracted_path,
            temp_directory_path / "packed.zip"
        )
        extracted_path = temp_directory_path / archived_path.stem
        shutil.unpack_archive(archived_path, extracted_path)

        is_equal, error_message = compare_directories(dummy_mapping_package_extracted_path, extracted_path)
        assert is_equal, f"Directory comparison failed:\n{error_message}"


def test_archive_extractor_pack_directory_nonexistent_source() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        with pytest.raises(FileNotFoundError):
            ArchiveExtractor().pack_directory(
                Path("nonexistent_dir"),
                temp_dir_path / "output.zip"
            )


def test_archive_extractor_pack_directory_source_is_file() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        test_file = temp_dir_path / "test.txt"
        test_file.touch()

        with pytest.raises(ValueError):
            ArchiveExtractor().pack_directory(test_file, temp_dir_path / "output.zip")


def test_archive_extractor_extract_folder_instead_of_archive() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        with pytest.raises(ValueError):
            ArchiveExtractor().extract(tmp_dir_path, tmp_dir_path)


def test_github_extractor_extract_success_with_default_args(
        dummy_github_project_path: Path,
        dummy_github_branch_name: str,
        dummy_repo_package_path: Path
) -> None:
    with setup_temporary_test_git_repository(dummy_github_project_path, dummy_github_branch_name) as repo_path:
        dest_path = Path(repo_path) / "test_destination"
        dest_path.mkdir(exist_ok=True)

        result_path = GitHubExtractor().extract(
            repository_url=str(repo_path),
            destination_path=dest_path,
            package_path=dummy_repo_package_path,
            branch_or_tag_name=dummy_github_branch_name
        )

        assert any(result_path.iterdir())


def test_github_extractor_extract_success_on_none_branch_or_tag_name(
        dummy_github_project_path: Path,
        dummy_repo_package_path: Path
) -> None:
    with setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        dest_path = Path(repo_path) / "test_destination"
        dest_path.mkdir(exist_ok=True)

        result_path = GitHubExtractor().extract(
            repository_url=str(repo_path),
            destination_path=dest_path,
            package_path=dummy_repo_package_path,
            branch_or_tag_name=None
        )

        assert any(result_path.iterdir())


def test_github_extractor_extract_temporary_success_with_branch_args_and_cleanup(
        dummy_github_project_path: Path,
        dummy_github_branch_name: str,
        dummy_packages_path_pattern: str
) -> None:
    """Test extract_temporary with cleanup. Note: branch_or_tag_name is not yet supported in extract_temporary."""
    with setup_temporary_test_git_repository(dummy_github_project_path, dummy_github_branch_name) as repo_path:
        with GitHubExtractor().extract_temporary(
                repository_url=str(repo_path),
                packages_path_pattern=dummy_packages_path_pattern,
                branch_or_tag_name=None  # extract_temporary doesn't support branch_or_tag_name yet
        ) as packages_path:
            assert len(packages_path) > 0
            for package_path in packages_path:
                assert package_path.match(dummy_packages_path_pattern)

        for package_path in packages_path:
            assert not package_path.exists()


def test_github_extractor_extract_temporary_fails_on_wrong_project_path(
        dummy_github_branch_name: str,
        dummy_packages_path_pattern: str
) -> None:
    with pytest.raises(ValueError):
        with GitHubExtractor().extract_temporary(
                repository_url="wrong/url",
                packages_path_pattern=dummy_packages_path_pattern,
                branch_or_tag_name=dummy_github_branch_name
        ):
            ...


def test_github_extractor_extract_temporary_fails_on_bad_pattern(
        dummy_github_project_path: Path,
        dummy_github_branch_name: str
) -> None:
    with pytest.raises(ValueError):
        with GitHubExtractor().extract_temporary(
                repository_url=dummy_github_project_path,
                packages_path_pattern="wrong*_pattern",
                branch_or_tag_name=dummy_github_branch_name
        ):
            ...


def test_github_extractor_extract_temporary_fails_on_wrong_tag_name(
        dummy_github_project_path: Path,
        dummy_packages_path_pattern: str
) -> None:
    with pytest.raises(ValueError):
        with GitHubExtractor().extract_temporary(
                repository_url=dummy_github_project_path,
                packages_path_pattern=dummy_packages_path_pattern,
                branch_or_tag_name="wrong_branch"
        ):
            ...


def test_github_extractor_extract_temporary_fails_on_none_project_path(
        dummy_github_branch_name: str,
        dummy_packages_path_pattern: str
) -> None:
    with pytest.raises(ValueError):
        with GitHubExtractor().extract_temporary(
                repository_url=None,
                packages_path_pattern=dummy_packages_path_pattern,
                branch_or_tag_name=dummy_github_branch_name
        ):
            ...


def test_github_extractor_extract_temporary_fails_on_none_pattern(
        dummy_github_project_path: Path,
        dummy_github_branch_name: str
) -> None:
    with pytest.raises(ValueError):
        with GitHubExtractor().extract_temporary(
                repository_url=dummy_github_project_path,
                packages_path_pattern=None,
                branch_or_tag_name=dummy_github_branch_name
        ):
            ...


def test_github_extractor_extract_fails_on_nonexistent_destination_path(
        dummy_github_branch_name: str,
        dummy_repo_package_path: Path
) -> None:
    with pytest.raises(ValueError):
        GitHubExtractor().extract(
            repository_url="dummy_url",
            destination_path=Path("non/existing/path"),
            package_path=dummy_repo_package_path,
            branch_or_tag_name=dummy_github_branch_name
        )


def test_github_extractor_extract_fails_on_empty_repo_url(
        dummy_github_branch_name: str,
        dummy_repo_package_path: Path
) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        with pytest.raises(ValueError):
            GitHubExtractor().extract(
                repository_url="",
                destination_path=tmp_dir_path,
                package_path=dummy_repo_package_path,
                branch_or_tag_name=dummy_github_branch_name
            )


def test_github_extractor_extract_fails_on_invalid_repo_url(
        dummy_github_branch_name: str,
        dummy_repo_package_path: Path,
        dummy_invalid_github_repo_url: str
) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        with pytest.raises(ValueError):
            GitHubExtractor().extract(
                repository_url=dummy_invalid_github_repo_url,
                destination_path=tmp_dir_path,
                package_path=dummy_repo_package_path,
                branch_or_tag_name=dummy_github_branch_name
            )


def test_github_extractor_extract_temporary_success_get_all_packages_pattern(
        dummy_github_project_path: Path,
        dummy_get_all_packages_pattern: str
) -> None:
    with setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        with GitHubExtractor().extract_temporary(
                repository_url=str(repo_path),
                packages_path_pattern=dummy_get_all_packages_pattern,
                branch_or_tag_name=None
        ) as packages_path:
            assert len(packages_path) > 0
            for package_path in packages_path:
                assert package_path.is_dir()


def test_mapping_package_extractor_abc_extract_not_implemented() -> None:
    class TestExtractor(ExtractorABC):
        def extract_temporary(self, *args, **kwargs):
            ...

    with pytest.raises(TypeError):
        TestExtractor()
