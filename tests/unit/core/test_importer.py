# test_importer.py
import zipfile

import pytest

from mssdk.core.adapters.package_importer import MappingPackageImporter, InvalidPackageStructure, \
    MappingPackageImportError


@pytest.fixture
def importer():
    """Create a MappingPackageImporter instance"""
    return MappingPackageImporter()


def test_import_zip_package(importer, zip_archive):
    """Test importing from ZIP archive"""
    package = importer.import_package(str(zip_archive))

    assert package.package_name == "package"
    assert package.package_version == "1.0.0"
    assert len(package.test_data.files) == 1
    assert len(package.transformation_data.technical_mappings) == 1
    assert len(package.validation_data.shacl_shapes) == 1
    assert len(package.validation_data.sparql_queries) == 1


def test_import_tar_package(importer, tar_archive):
    """Test importing from TAR archive"""
    package = importer.import_package(str(tar_archive))

    assert package.package_name == "package"
    assert len(package.test_data.files) == 1


def test_import_rar_package(importer, rar_archive):
    """Test importing from RAR archive"""
    package = importer.import_package(str(rar_archive))

    assert package.package_name == "package"
    assert len(package.test_data.files) == 1


def test_invalid_package_structure(importer, tmp_path):
    """Test importing package with invalid structure"""
    # Create archive with missing required folders
    archive_path = tmp_path / "invalid.zip"
    with zipfile.ZipFile(archive_path, 'w') as zf:
        zf.writestr('some_file.txt', 'content')

    with pytest.raises(InvalidPackageStructure):
        importer.import_package(str(archive_path))


def test_missing_conceptual_mapping(importer, tmp_path, test_files):
    """Test importing package without conceptual mapping"""
    # Remove conceptual mapping from test files
    files = test_files.copy()
    del files['transformation/mapping.xlsx']

    # Create archive
    archive_path = tmp_path / "invalid.zip"
    with zipfile.ZipFile(archive_path, 'w') as zf:
        for name, content in files.items():
            zf.writestr(name, content)

    with pytest.raises(InvalidPackageStructure):
        importer.import_package(str(archive_path))


@pytest.mark.parametrize("file_path", [
    "nonexistent.zip",
    "invalid_format.xyz"
])
def test_invalid_archive_path(importer, file_path):
    """Test importing from invalid archive path"""
    with pytest.raises(MappingPackageImportError):
        importer.import_package(file_path)


def test_large_package(importer, tmp_path):
    """Test importing large package with many files"""
    # Create a large number of test files
    files = {}
    for i in range(100):
        files[f'test/file{i}.xml'] = b'<?xml version="1.0"?><root><data>Test</data></root>'

    # Create archive
    archive_path = tmp_path / "large_package.zip"
    with zipfile.ZipFile(archive_path, 'w') as zf:
        for name, content in files.items():
            zf.writestr(name, content)

    package = importer.import_package(str(archive_path))
    assert len(package.test_data.files) == 100