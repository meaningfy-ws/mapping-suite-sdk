# test_handlers.py
import pytest

from mssdk.core.adapters.package_importer import ZipHandler, TarHandler, RarHandler, UnsupportedArchiveFormat, \
    MappingPackageImportError


def test_zip_handler(zip_archive, test_files):
    """Test ZIP archive handler"""
    handler = ZipHandler()
    files = handler.handle(str(zip_archive))

    assert len(files) == len(test_files)
    assert all(name in files for name in test_files)
    assert all(files[name] == content for name, content in test_files.items())


def test_tar_handler(tar_archive, test_files):
    """Test TAR archive handler"""
    handler = TarHandler()
    files = handler.handle(str(tar_archive))

    assert len(files) == len(test_files)
    assert all(name in files for name in test_files)
    assert all(files[name] == content for name, content in test_files.items())


def test_rar_handler(rar_archive, test_files):
    """Test RAR archive handler"""
    handler = RarHandler()
    files = handler.handle(str(rar_archive))

    assert len(files) == len(test_files)
    assert all(name in files for name in test_files)
    assert all(files[name] == content for name, content in test_files.items())


def test_handler_chain():
    """Test handler chain of responsibility"""
    zip_handler = ZipHandler()
    rar_handler = RarHandler()
    tar_handler = TarHandler()

    zip_handler.set_next(rar_handler).set_next(tar_handler)

    with pytest.raises(UnsupportedArchiveFormat):
        zip_handler.handle("invalid.xyz")


def test_invalid_archive(tmp_path):
    """Test handling invalid archive files"""
    invalid_zip = tmp_path / "invalid.zip"
    invalid_zip.write_bytes(b"invalid content")

    handler = ZipHandler()
    with pytest.raises(MappingPackageImportError):
        handler.handle(str(invalid_zip))