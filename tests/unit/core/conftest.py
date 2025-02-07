# conftest.py
import pytest
import os
import zipfile
import tarfile
import rarfile
import pandas as pd
import io
from pathlib import Path

@pytest.fixture
def test_files():
    """Create test files content"""
    return {
        'test/sample.xml': b'<?xml version="1.0"?><root><data>Test</data></root>',
        'transformation/mapping.xlsx': _create_excel_content(),
        'transformation/technical.ttl': b'@prefix ex: <http://example.org/> .\nex:Resource1 a ex:Type1 .',
        'validation/shape.ttl': b'@prefix sh: <http://www.w3.org/ns/shacl#> .\nex:Shape1 a sh:NodeShape .',
        'validation/query.rq': b'SELECT ?s WHERE { ?s a ?type }'
    }

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with test files"""
    for path, content in test_files().items():
        file_path = tmp_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
    return tmp_path

@pytest.fixture
def zip_archive(temp_dir, tmp_path):
    """Create a ZIP archive with test files"""
    archive_path = tmp_path / "package.zip"
    with zipfile.ZipFile(archive_path, 'w') as zf:
        for path in temp_dir.rglob('*'):
            if path.is_file():
                zf.write(path, path.relative_to(temp_dir))
    return archive_path

@pytest.fixture
def tar_archive(temp_dir, tmp_path):
    """Create a TAR archive with test files"""
    archive_path = tmp_path / "package.tar.gz"
    with tarfile.open(archive_path, 'w:gz') as tf:
        for path in temp_dir.rglob('*'):
            if path.is_file():
                tf.add(path, path.relative_to(temp_dir))
    return archive_path

@pytest.fixture
def rar_archive(temp_dir, tmp_path):
    """Create a RAR archive with test files"""
    archive_path = tmp_path / "package.rar"
    with rarfile.RarFile(archive_path, 'w') as rf:
        for path in temp_dir.rglob('*'):
            if path.is_file():
                rf.write(path, path.relative_to(temp_dir))
    return archive_path

def _create_excel_content():
    """Create a sample Excel file content"""
    df = pd.DataFrame({
        'source': ['field1', 'field2'],
        'target': ['concept1', 'concept2']
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()