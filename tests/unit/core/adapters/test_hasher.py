import hashlib

import pytest

from mapping_suite_sdk.core.adapters.hasher import HasherABC, SHA256Hasher, MappingPackageHasher


def test_sha256_hasher_hash_returns_correct_hash():
    hasher = SHA256Hasher()
    content = b"test content"
    expected_hash = hashlib.sha256(content).hexdigest()

    result = hasher.hash(content)

    assert result == expected_hash
    assert isinstance(result, str)


def test_sha256_hasher_hash_empty_content():
    hasher = SHA256Hasher()
    content = b""
    expected_hash = hashlib.sha256(content).hexdigest()

    result = hasher.hash(content)

    assert result == expected_hash
    assert len(result) == 64  # SHA256 hash length


def test_sha256_hasher_hash_different_content_different_hash():
    hasher = SHA256Hasher()
    content1 = b"test content 1"
    content2 = b"test content 2"

    hash1 = hasher.hash(content1)
    hash2 = hasher.hash(content2)

    assert hash1 != hash2
    assert len(hash1) == 64
    assert len(hash2) == 64


def test_sha256_hasher_hash_same_content_same_hash():
    hasher = SHA256Hasher()
    content = b"consistent test content"

    hash1 = hasher.hash(content)
    hash2 = hasher.hash(content)

    assert hash1 == hash2


def test_sha256_hasher_hash_large_content():
    hasher = SHA256Hasher()
    content = b"x" * 1000000  # 1MB of data

    result = hasher.hash(content)

    assert isinstance(result, str)
    assert len(result) == 64


def test_sha256_hasher_hash_unicode_content():
    hasher = SHA256Hasher()
    content = "test unicode content: 你好世界".encode('utf-8')

    result = hasher.hash(content)

    assert isinstance(result, str)
    assert len(result) == 64


def test_hasher_abc_cannot_be_instantiated():
    with pytest.raises(TypeError):
        HasherABC()


def test_hasher_abc_subclass_must_implement_hash():
    class IncompleteHasher(HasherABC):
        ...

    with pytest.raises(TypeError):
        IncompleteHasher()


def test_hasher_abc_subclass_with_hash_implementation():
    class CustomHasher(HasherABC):
        def hash(self, content: bytes) -> str:
            return "custom_hash"

    hasher = CustomHasher()
    result = hasher.hash(b"any content")

    assert result == "custom_hash"


def test_mapping_package_hasher_abc_cannot_be_instantiated():
    with pytest.raises(TypeError):
        MappingPackageHasher()


def test_mapping_package_hasher_abc_subclass_must_implement_hash():
    class IncompleteMappingPackageHasher(MappingPackageHasher):
        ...

    with pytest.raises(TypeError):
        IncompleteMappingPackageHasher()


def test_mapping_package_hasher_abc_subclass_with_hash_implementation():
    class CustomMappingPackageHasher(MappingPackageHasher):
        def hash(self, with_version=None) -> str:
            return f"custom_mapping_hash_{with_version}"

    hasher = CustomMappingPackageHasher()
    result = hasher.hash()

    assert result == "custom_mapping_hash_None"


def test_mapping_package_hasher_abc_subclass_with_version_parameter():
    class CustomMappingPackageHasher(MappingPackageHasher):
        def hash(self, with_version=None) -> str:
            return f"hash_version_{with_version or 'default'}"

    hasher = CustomMappingPackageHasher()
    result_no_version = hasher.hash()
    result_with_version = hasher.hash(with_version="1.0.0")

    assert result_no_version == "hash_version_default"
    assert result_with_version == "hash_version_1.0.0"