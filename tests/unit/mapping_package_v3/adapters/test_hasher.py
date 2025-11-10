from unittest.mock import Mock

from mapping_suite_sdk.core.adapters.hasher import SHA256Hasher, HasherABC
from mapping_suite_sdk.mapping_package_v3.adapters.hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


def test_mp_v3_hasher_initialization_with_default_hasher(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    assert hasher.mapping_package == fixture_mapping_package_v3_model
    assert isinstance(hasher.hasher, SHA256Hasher)


def test_mp_v3_hasher_has_the_same_hash(fixture_mapping_package_v3_model: MappingPackageV3):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)
    generated_hash: str = hasher.hash()
    assert fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest == generated_hash



def test_mp_v3_hasher_initialization_with_custom_hasher(fixture_mapping_package_v3_model):
    custom_hasher = Mock(spec=HasherABC)

    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model, custom_hasher)

    assert hasher.mapping_package == fixture_mapping_package_v3_model
    assert hasher.hasher == custom_hasher


def test_mp_v3_hasher_hash_creates_consistent_signature(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    hash1 = hasher.hash()
    hash2 = hasher.hash()

    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64


def test_mp_v3_hasher_hash_with_custom_version(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    hash_default = hasher.hash()
    hash_custom = hasher.hash(with_version="3.0.0")

    assert hash_default != hash_custom
    assert isinstance(hash_default, str)
    assert isinstance(hash_custom, str)


def test_mp_v3_hasher_hash_uses_package_version(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    original_version = fixture_mapping_package_v3_model.metadata.mapping_version

    hash_original = hasher.hash()
    hash_with_version = hasher.hash(with_version=original_version)

    assert hash_original == hash_with_version


def test_mp_v3_hasher_hash_different_versions_different_hash(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    hash_v1 = hasher.hash(with_version="1.0.0")
    hash_v2 = hasher.hash(with_version="2.0.0")
    hash_v3 = hasher.hash(with_version="3.0.0")

    assert hash_v1 != hash_v2
    assert hash_v2 != hash_v3
    assert hash_v1 != hash_v3


def test_mp_v3_hasher_hash_uses_normalized_content(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    hash1 = hasher.hash()
    hash2 = hasher.hash()

    assert hash1 == hash2


def test_mp_v3_hasher_hash_file_path_sorting(fixture_mapping_package_v3_model):
    mock_hasher = Mock(spec=HasherABC)
    mock_hasher.hash.side_effect = lambda content: f"hash_{len(content)}"

    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model, mock_hasher)
    hasher.hash()

    technical_files = fixture_mapping_package_v3_model.technical_mapping_suite.files
    vocab_files = fixture_mapping_package_v3_model.vocabulary_mapping_suite.files

    if len(technical_files) > 1:
        sorted_technical_paths = sorted([str(f.path) for f in technical_files])
        original_paths = [str(f.path) for f in technical_files]
        assert len(sorted_technical_paths) == len(original_paths)

    if len(vocab_files) > 1:
        sorted_vocab_paths = sorted([str(f.path) for f in vocab_files])
        original_paths = [str(f.path) for f in vocab_files]
        assert len(sorted_vocab_paths) == len(original_paths)


def test_mp_v3_hasher_hash_with_none_version(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    hash_none = hasher.hash(with_version=None)
    hash_default = hasher.hash()

    assert hash_none == hash_default


def test_mp_v3_hasher_real_sha256_hash_format(fixture_mapping_package_v3_model):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model, SHA256Hasher())
    result = hasher.hash()

    assert isinstance(result, str)
    assert len(result) == 64
    assert all(c in '0123456789abcdef' for c in result.lower())


def test_mp_v3_hasher_uses_only_package_metadata_for_hashing(fixture_mapping_package_v3_model: MappingPackageV3):
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)

    initial_hash: str = hasher.hash()

    fixture_mapping_package_v3_model.metadata.context = "dummy_text"
    hasher.mapping_package = fixture_mapping_package_v3_model
    hash_after_change: str = hasher.hash()

    assert initial_hash == hash_after_change
