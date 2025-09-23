import importlib.metadata
import logging

from mapping_suite_sdk.core.adapters.extractor import MappingPackageExtractorABC, ArchivePackageExtractor, \
    GithubPackageExtractor
from mapping_suite_sdk.core.adapters.hasher import HasherABC, SHA256Hasher, MappingPackageHasher
from mapping_suite_sdk.core.adapters.loader import MappingPackageAssetLoader, TechnicalMappingSuiteLoader, \
    VocabularyMappingSuiteLoader, TestDataSuitesLoader, SPARQLTestSuitesLoader, SHACLTestSuitesLoader, \
    TestResultSuiteLoader, ConceptualMappingFileLoader
from mapping_suite_sdk.core.adapters.repository import RepositoryError, ModelNotFoundError, RepositoryABC, \
    MongoDBRepository
from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser, \
    TechnicalMappingCollectionAssetSerialiser, VocabularyMappingCollectionAssetSerialiser, \
    TestDataCollectionAssetSerialiser, SAPRQLTestCollectionAssetSerialiser, SHACLTestCollectionAssetSerialiser, \
    ConceptualMappingFileAssetSerialiser, TestResultCollectionAssetSerialiser
from mapping_suite_sdk.core.adapters.tracer import add_span_processor_to_mssdk_tracer_provider, set_mssdk_tracing, \
    get_mssdk_tracing, is_mssdk_tracing_enabled, traced_routine, traced_class
from mapping_suite_sdk.core.adapters.validator_abc import MPValidationException, MPValidationStepABC
from mapping_suite_sdk.core.models.collection_asset import CollectionAsset, VocabularyMappingCollectionAsset, \
    TechnicalMappingCollectionAsset, TestDataCollectionAsset, SAPRQLTestCollectionAsset, SHACLShapesCollectionAsset, \
    SHACLTestCollectionAsset, TestDataResultCollectionAsset, TestResultCollectionAsset
from mapping_suite_sdk.core.models.file_asset import FileAsset, ConceptualMappingFileAsset, VocabularyMappingFileAsset, \
    SPARQLQueryFileAsset, SHACLShapesFileAsset, SHACLShapesResultQueryFileAsset, TestDataFileAsset, \
    TestDataResultFileAsset, TechnicalMappingFileAsset, RMLMappingFileAsset, YARRRMLMappingFileAsset, ReportFileAsset
from mapping_suite_sdk.core.models.mapping_package import MappingPackage
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.core.models.pydantic import PydanticModel, fields
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_hasher import MappingPackageV1Hasher
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader import MappingPackageV1MetadataLoader, \
    MappingPackageV1Loader
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_serialiser import MappingPackageV1MetadataSerialiser, \
    MappingPackageV1Serialiser
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_validator import MPV1StructuralValidationStep, \
    MPV1HashValidationStep, MappingPackageV1Validator
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1_metadata import \
    MappingPackageV1EligibilityConstraints, MappingPackageV1Metadata
from mapping_suite_sdk.mapping_package_v1.services.load_mapping_package_v1 import load_mapping_package_v1_from_folder, \
    load_mapping_package_v1_from_archive, load_mapping_packages_v1_from_github, load_mapping_package_v1_from_mongo_db
from mapping_suite_sdk.mapping_package_v1.services.serialise_mapping_package_v1 import serialise_mapping_package_v1, \
    serialise_mapping_package_v1_to_folder
from mapping_suite_sdk.mapping_package_v1.services.validate_mapping_package_v1 import validate_mapping_package_v1, \
    validate_mapping_package_v1_from_archive, validate_mapping_package_v1_from_folder, \
    validate_bulk_mapping_packages_v1_from_folder, validate_bulk_mapping_packages_v1_from_github
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_hasher import MappingPackageV2Hasher
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader import MappingPackageV2MetadataLoader, \
    MappingPackageV2Loader
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_serialiser import MappingPackageV2MetadataSerialiser, \
    MappingPackageV2Serialiser
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_validator import MPV2StructuralValidationStep, \
    MPV2HashValidationStep, MappingPackageV2Validator
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import \
    MappingPackageV2EligibilityConstraints, MappingPackageV2Metadata
from mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2 import load_mapping_package_v2_from_folder, \
    load_mapping_package_v2_from_archive, load_mapping_packages_v2_from_github, load_mapping_package_v2_from_mongo_db
from mapping_suite_sdk.mapping_package_v2.services.serialise_mapping_package_v2 import serialise_mapping_package_v2, \
    serialise_mapping_package_v2_to_folder
from mapping_suite_sdk.mapping_package_v2.services.validate_mapping_package_v2 import validate_mapping_package_v2, \
    validate_mapping_package_v2_from_archive, validate_mapping_package_v2_from_folder, \
    validate_bulk_mapping_packages_v2_from_folder, validate_bulk_mapping_packages_v2_from_github
from mapping_suite_sdk.utils import load_file_by_extensions, write_file_by_content_type, normalize_content
from mapping_suite_sdk.vars import MSSDK_LOGGING_STRING_FORMAT, MSSDK_DATE_FORMAT

logging.basicConfig(level=logging.INFO,
                    format=MSSDK_LOGGING_STRING_FORMAT,
                    datefmt=MSSDK_DATE_FORMAT)

__version__ = importlib.metadata.version('mapping-suite-sdk')

__all__ = [

    ### Core
    ## Adapters
    # extractor.py
    "MappingPackageExtractorABC",
    "ArchivePackageExtractor",
    "GithubPackageExtractor",

    # hasher.py
    "HasherABC",
    "SHA256Hasher",
    "MappingPackageHasher",

    # loader.py
    "MappingPackageAssetLoader",
    "TechnicalMappingSuiteLoader",
    "VocabularyMappingSuiteLoader",
    "TestDataSuitesLoader",
    "SPARQLTestSuitesLoader",
    "SHACLTestSuitesLoader",
    "TestResultSuiteLoader",
    "ConceptualMappingFileLoader",

    # repository.py
    "RepositoryError",
    "ModelNotFoundError",
    "RepositoryABC",
    "MongoDBRepository",

    # serialiser.py
    "MappingPackageAssetSerialiser",
    "TechnicalMappingCollectionAssetSerialiser",
    "VocabularyMappingCollectionAssetSerialiser",
    "TestDataCollectionAssetSerialiser",
    "SAPRQLTestCollectionAssetSerialiser",
    "SHACLTestCollectionAssetSerialiser",
    "ConceptualMappingFileAssetSerialiser",
    "TestResultCollectionAssetSerialiser",

    # tracer.py
    "add_span_processor_to_mssdk_tracer_provider",
    "set_mssdk_tracing",
    "get_mssdk_tracing",
    "is_mssdk_tracing_enabled",
    "traced_routine",
    "traced_class",

    # validator_abc.py
    "MPValidationException",
    "MPValidationStepABC",

    ## Models
    # collection_asset.py
    "CollectionAsset",
    "VocabularyMappingCollectionAsset",
    "TechnicalMappingCollectionAsset",
    "TestDataCollectionAsset",
    "SAPRQLTestCollectionAsset",
    "SHACLShapesCollectionAsset",
    "SHACLTestCollectionAsset",
    "TestDataResultCollectionAsset",
    "TestResultCollectionAsset",

    # file_asset.py
    "FileAsset",
    "ConceptualMappingFileAsset",
    "VocabularyMappingFileAsset",
    "SPARQLQueryFileAsset",
    "SHACLShapesFileAsset",
    "SHACLShapesResultQueryFileAsset",
    "TestDataFileAsset",
    "TestDataResultFileAsset",
    "TechnicalMappingFileAsset",
    "RMLMappingFileAsset",
    "YARRRMLMappingFileAsset",
    "ReportFileAsset",

    # mapping_package.py
    "MappingPackage",

    # mapping_package_metadata.py
    "MappingPackageMetadata",

    # pydantic.py
    "PydanticModel",
    "fields",

    ### Mapping Package V1
    ## Adapters
    # mp_v1_hasher.py
    "MappingPackageV1Hasher",

    # mp_v1_loader.py
    "MappingPackageV1MetadataLoader",
    "MappingPackageV1Loader",

    # mp_v1_serialiser.py
    "MappingPackageV1MetadataSerialiser",
    "MappingPackageV1Serialiser",

    # mp_v1_validator.py
    "MPV1StructuralValidationStep",
    "MPV1HashValidationStep",
    "MappingPackageV1Validator",

    ## Models
    # mapping_package_v1.py
    "MappingPackageV1",

    # mapping_package_v1_metadata.py
    "MappingPackageV1EligibilityConstraints",
    "MappingPackageV1Metadata",

    ## Services
    # load_mapping_package_v1.py
    "load_mapping_package_v1_from_folder",
    "load_mapping_package_v1_from_archive",
    "load_mapping_packages_v1_from_github",
    "load_mapping_package_v1_from_mongo_db",

    # serialise_mapping_package_v1.py
    "serialise_mapping_package_v1",
    "serialise_mapping_package_v1_to_folder",

    # validate_mapping_package_v1.py
    "validate_mapping_package_v1",
    "validate_mapping_package_v1_from_archive",
    "validate_mapping_package_v1_from_folder",
    "validate_bulk_mapping_packages_v1_from_folder",
    "validate_bulk_mapping_packages_v1_from_github",

    ### Mapping Package V2
    ## Adapters
    # mp_v2_hasher.py
    "MappingPackageV2Hasher",

    # mp_v2_loader.py
    "MappingPackageV2MetadataLoader",
    "MappingPackageV2Loader",

    # mp_v2_serialiser.py
    "MappingPackageV2MetadataSerialiser",
    "MappingPackageV2Serialiser",

    # mp_v2_validator.py
    "MPV2StructuralValidationStep",
    "MPV2HashValidationStep",
    "MappingPackageV2Validator",

    ## Models
    # mapping_package_v2.py
    "MappingPackageV2",

    # mapping_package_v2_metadata.py
    "MappingPackageV2EligibilityConstraints",
    "MappingPackageV2Metadata",

    ## Services
    # load_mapping_package_v2.py
    "load_mapping_package_v2_from_folder",
    "load_mapping_package_v2_from_archive",
    "load_mapping_packages_v2_from_github",
    "load_mapping_package_v2_from_mongo_db",

    # serialise_mapping_package_v2.py
    "serialise_mapping_package_v2",
    "serialise_mapping_package_v2_to_folder",

    # validate_mapping_package_v2.py
    "validate_mapping_package_v2",
    "validate_mapping_package_v2_from_archive",
    "validate_mapping_package_v2_from_folder",
    "validate_bulk_mapping_packages_v2_from_folder",
    "validate_bulk_mapping_packages_v2_from_github",

    # utils.py
    "load_file_by_extensions",
    "write_file_by_content_type",
    "normalize_content",

    # Other
    "__version__"
]
