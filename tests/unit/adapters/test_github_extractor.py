import shutil
import tempfile
from pathlib import Path

from git import Repo

from mapping_suite_sdk.adapters.extractor import GithubPackageExtractor


def test_github_extractor_success_with_default_args(dummy_github_project_path: Path,
                                                    dummy_github_branch_name: str,
                                                    dummy_repo_package_path: Path) -> None:
    # Setup
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / dummy_github_project_path.name
        shutil.copytree(dummy_github_project_path, repo_path)
        repo = Repo.init(repo_path)
        repo.git.add(all=True)
        repo.index.commit("commit for test")
        repo.create_tag(dummy_github_branch_name)
        # Execute
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            result_path = GithubPackageExtractor().extract(repository_url=str(repo_path),
                                                           destination_path=temp_dir_path,
                                                           package_path=dummy_repo_package_path,
                                                           branch_or_tag_name=dummy_github_branch_name)
            # Assert
            assert any(result_path.iterdir())


def test_github_extractor_success_with_branch_args_and_cleanup(dummy_github_project_path: Path,
                                                               dummy_github_branch_name: str,
                                                               dummy_packages_path_pattern: str) -> None:
    # Setup
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / dummy_github_project_path.name
        shutil.copytree(dummy_github_project_path, repo_path)
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
