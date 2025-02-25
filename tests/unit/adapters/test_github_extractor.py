import shutil
import tempfile
from pathlib import Path

import pytest
from git import Repo

from mapping_suite_sdk.adapters.extractor import GithubPackageExtractor


def test_github_extractor_success_with_default_args(dummy_github_project_path: Path,
                                                    dummy_github_branch_name: str,
                                                    dummy_repo_package_path: Path) -> None:
    # Setup
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        repo_path = tmp_dir_path / dummy_github_project_path.name
        repo_path = shutil.copytree(dummy_github_project_path, repo_path)
        repo = Repo.init(repo_path)
        repo.git.add(all=True)
        repo.index.commit("commit for test")
        repo.create_tag(dummy_github_branch_name)
        # Execute
        dest_path: Path = tmp_dir_path / "test_destination"
        dest_path.mkdir(exist_ok=True)
        result_path = GithubPackageExtractor().extract(repository_url=str(repo_path),
                                                       destination_path=dest_path,
                                                       package_path=dummy_repo_package_path,
                                                       branch_or_tag_name=dummy_github_branch_name)
        # Assert
        assert any(result_path.iterdir())


def test_github_extract_temporary_success_with_branch_args_and_cleanup(dummy_github_project_path: Path,
                                                                       dummy_github_branch_name: str,
                                                                       dummy_packages_path_pattern: str) -> None:
    # Setup
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / dummy_github_project_path.name
        repo_path = shutil.copytree(dummy_github_project_path, repo_path)
        repo = Repo.init(repo_path)
        repo.git.add(all=True)
        repo.index.commit("commit for test")
        repo.create_tag(dummy_github_branch_name)
        # Execute
        with GithubPackageExtractor().extract_temporary(repository_url=str(repo_path),
                                                        packages_path_pattern=dummy_packages_path_pattern,
                                                        branch_or_tag_name=dummy_github_branch_name) as packages_path:
            # Assert
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


def test_github_extract_temporary_fails_on_empty_project_path(dummy_github_branch_name: str,
                                                              dummy_packages_path_pattern: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url=None,
                                                        packages_path_pattern=dummy_packages_path_pattern,
                                                        branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_temporary_fails_on_empty_pattern(dummy_github_project_path: Path,
                                                         dummy_github_branch_name: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract_temporary(repository_url=dummy_github_project_path,
                                                        packages_path_pattern=None,
                                                        branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_fails_on_not_existing_dest_path(dummy_github_branch_name: str,
                                                        dummy_packages_path_pattern: str) -> None:
    with pytest.raises(ValueError):
        with GithubPackageExtractor().extract(repository_url="",
                                              destination_path=Path("non/existing/path"),
                                              package_path=Path(""),
                                              branch_or_tag_name=dummy_github_branch_name):
            pass


def test_github_extract_fails_on_not_existing_repo_url(dummy_github_branch_name: str,
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
