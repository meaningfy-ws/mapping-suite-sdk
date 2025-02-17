import filecmp
import json
import shutil
import tempfile
from pathlib import Path
from typing import Set

from mssdk.adapters.serialiser import MappingPackageSerializer
from mssdk.models.mapping_package import MappingPackage


def _get_all_files(directory: Path) -> Set[str]:
    """Get all files in directory recursively, returning relative paths."""
    return {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}


def _compare_json_files(file1: Path, file2: Path) -> bool:
    """Compare two JSON files for semantic equality."""
    with file1.open() as f1, file2.open() as f2:
        return json.load(f1) == json.load(f2)


def _compare_directories(source_dir: Path, target_dir: Path) -> tuple[bool, str]:
    """
    Compare directories recursively, allowing target_dir to have extra files.
    source_dir: the serialized folder (all files must exist in target)
    target_dir: the dummy package folder (can have extra files)
    Returns (is_equal, error_message)
    """

    source_files = _get_all_files(source_dir)
    target_files = _get_all_files(target_dir)

    missing_files = source_files - target_files
    if missing_files:
        return False, f"Files missing in {target_dir}:\n" + "\n".join(sorted(missing_files))

    for rel_path in source_files:
        source_file = source_dir / rel_path
        target_file = target_dir / rel_path

        if source_file.suffix.lower() == '.json':
            try:
                if not _compare_json_files(source_file, target_file):
                    return False, f"JSON content differs in {rel_path}"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON in {rel_path}: {str(e)}"
        else:
            # Binary comparison for other files
            if not filecmp.cmp(str(source_file), str(target_file), shallow=False):
                return False, f"Content differs in {rel_path}"

    return True, ""


def test_serialiser_generates_same_output(dummy_mapping_package_model: MappingPackage,
                                          dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_directory_path = Path(temp_directory)

        serialised_folder_path: Path = temp_directory_path / "serialised_path"
        serialised_folder_path.mkdir(parents=False, exist_ok=True)

        temp_mp_path = temp_directory_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir(parents=False, exist_ok=True)

        shutil.unpack_archive(dummy_mapping_package_path, temp_mp_path)

        MappingPackageSerializer().serialize(serialised_folder_path, dummy_mapping_package_model)

        is_equal, error_message = _compare_directories(serialised_folder_path, temp_mp_path)
        assert is_equal, f"Directory comparison failed:\n{error_message}"
