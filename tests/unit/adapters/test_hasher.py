from mapping_suite_sdk.adapters.hasher import MappingPackageHasher
from mapping_suite_sdk.models.mapping_package import MappingPackage
from tests.conftest import _get_random_string


def test_hasher_generates_same_hash(dummy_mapping_package_model: MappingPackage):
    hasher = MappingPackageHasher(mapping_package=dummy_mapping_package_model)
    result_hash = hasher.hash_mapping_package()

    assert result_hash == dummy_mapping_package_model.metadata.signature

    result_hash = hasher.hash_mapping_package(with_version=dummy_mapping_package_model.metadata.mapping_version)

    assert result_hash == dummy_mapping_package_model.metadata.signature

def test_hasher_generates_different_hash_on_data_changes(dummy_mapping_package_model: MappingPackage):
    random_string = _get_random_string()
    hasher = MappingPackageHasher(mapping_package=dummy_mapping_package_model)
    result_hash = hasher.hash_mapping_package()

    assert result_hash == dummy_mapping_package_model.metadata.signature

    assert random_string != dummy_mapping_package_model.metadata.description
    dummy_mapping_package_model.metadata.description = random_string

    result_hash = hasher.hash_mapping_package()
    assert result_hash != dummy_mapping_package_model.metadata.signature