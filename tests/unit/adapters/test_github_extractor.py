import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.adapters.extractor import GithubPackageExtractor
from tests.conftest import _setup_temporary_test_git_repository


def test_github_extractor_success_with_default_args(dummy_github_project_path: Path,
                                                    dummy_github_branch_name: str,
                                                    dummy_repo_package_path: Path) -> None:
    # Setup
    with _setup_temporary_test_git_repository(dummy_github_project_path, dummy_github_branch_name) as repo_path:
        # Execute
        dest_path: Path = Path(repo_path) / "test_destination"
        dest_path.mkdir(exist_ok=True)
        result_path = GithubPackageExtractor().extract(repository_url=str(repo_path),
                                                       destination_path=dest_path,
                                                       package_path=dummy_repo_package_path,
                                                       branch_or_tag_name=dummy_github_branch_name)
        # Assert
        assert any(result_path.iterdir())


def test_github_extractor_success_on_none_branch_or_tag_name(dummy_github_project_path: Path,
                                                             dummy_repo_package_path: Path) -> None:
    # Setup
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        # Execute
        dest_path: Path = Path(repo_path) / "test_destination"
        dest_path.mkdir(exist_ok=True)
        result_path = GithubPackageExtractor().extract(repository_url=str(repo_path),
                                                       destination_path=dest_path,
                                                       package_path=dummy_repo_package_path,
                                                       branch_or_tag_name=None)
        # Assert
        assert any(result_path.iterdir())


def test_github_extract_temporary_success_with_branch_args_and_cleanup(dummy_github_project_path: Path,
                                                                       dummy_github_branch_name: str,
                                                                       dummy_packages_path_pattern: str) -> None:
    with _setup_temporary_test_git_repository(dummy_github_project_path, dummy_github_branch_name) as repo_path:
        with GithubPackageExtractor().extract_temporary(repository_url=str(repo_path),
                                                        packages_path_pattern=dummy_packages_path_pattern,
                                                        branch_or_tag_name=dummy_github_branch_name) as packages_path:
            assert len(packages_path) > 0
            for package_path in packages_path:
                assert package_path.match(dummy_packages_path_pattern)

        for package_path in packages_path:
            assert not package_path.exists()


def test_github_extract_temporary_fails_on_wrong_project_path(dummy_github_branch_name: str,
                                                              dummy_packages_path_pattern: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url="wrong/url",
                                                        packages_path_pattern=dummy_packages_path_pattern,
                                                        branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_temporary_fails_on_bad_pattern(dummy_github_project_path: Path,
                                                       dummy_github_branch_name: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url=dummy_github_project_path,
                                                        packages_path_pattern="wrong*_pattern",
                                                        branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_temporary_fails_on_wrong_tag_name(dummy_github_project_path: Path,
                                                          dummy_packages_path_pattern: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url=dummy_github_project_path,
                                                        packages_path_pattern=dummy_packages_path_pattern,
                                                        branch_or_tag_name="wrong_branch"):
            pass


def test_github_extract_temporary_fails_on_none_project_path(dummy_github_branch_name: str,
                                                             dummy_packages_path_pattern: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url=None,
                                                        packages_path_pattern=dummy_packages_path_pattern,
                                                        branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_temporary_fails_on_none_pattern(dummy_github_project_path: Path,
                                                        dummy_github_branch_name: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url=dummy_github_project_path,
                                                        packages_path_pattern=None,
                                                        branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_fails_on_empty_dest_path(dummy_github_branch_name: str,
                                                 dummy_packages_path_pattern: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract(repository_url="",
                                              destination_path=Path("non/existing/path"),
                                              package_path=Path(""),
                                              branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_fails_on_empty_repo_url(dummy_github_branch_name: str,
                                                dummy_repo_package_path: Path,
                                                dummy_packages_path_pattern: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        with pytest.raises(ValueError):
            with GithubPackageExtractor().extract(repository_url="",
                                                  destination_path=tmp_dir_path,
                                                  package_path=dummy_repo_package_path,
                                                  branch_or_tag_name=dummy_github_branch_name):
                pass


def test_github_extract_fails_on_invalid_repo_url(dummy_github_branch_name: str,
                                                  dummy_repo_package_path: Path,
                                                  dummy_invalid_github_repo_url: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        with pytest.raises(ValueError):
            with GithubPackageExtractor().extract(repository_url=dummy_invalid_github_repo_url,
                                                  destination_path=tmp_dir_path,
                                                  package_path=dummy_repo_package_path,
                                                  branch_or_tag_name=dummy_github_branch_name):
                pass
