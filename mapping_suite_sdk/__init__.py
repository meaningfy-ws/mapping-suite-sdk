import importlib.metadata
import logging

from mapping_suite_sdk.adapters.extractor import (ArchivePackageExtractor,
                                                  GithubPackageExtractor
                                                  )
from mapping_suite_sdk.adapters.hasher import (MappingPackageHasher)
from mapping_suite_sdk.adapters.loader import (TechnicalMappingSuiteLoader,
                                               VocabularyMappingSuiteLoader,
                                               TestDataSuitesLoader,
                                               SPARQLTestSuitesLoader,
                                               SHACLTestSuitesLoader,
                                               MappingPackageMetadataLoader,
                                               MappingPackageIndexLoader,
                                               TestResultSuiteLoader,
                                               ConceptualMappingFileLoader,
                                               MappingPackageLoader
                                               )
from mapping_suite_sdk.adapters.repository import (MongoDBRepository,
                                                   )
from mapping_suite_sdk.adapters.serialiser import (TechnicalMappingSuiteSerialiser,
                                                   VocabularyMappingSuiteSerialiser,
                                                   TestDataSuitesSerialiser,
                                                   SPARQLTestSuitesSerialiser,
                                                   SHACLTestSuitesSerialiser,
                                                   MappingPackageMetadataSerialiser,
                                                   ConceptualMappingFileSerialiser,
                                                   MappingPackageSerialiser
                                                   )
from mapping_suite_sdk.adapters.tracer import (add_span_processor_to_mssdk_tracer_provider,
                                               set_mssdk_tracing,
                                               get_mssdk_tracing,
                                               )
from mapping_suite_sdk.adapters.validator import (MappingPackageValidator)
from mapping_suite_sdk.services.load_mapping_package import (load_mapping_package_from_folder,
                                                             load_mapping_package_from_archive,
                                                             load_mapping_packages_from_github,
                                                             load_mapping_package_from_mongo_db
                                                             )
from mapping_suite_sdk.services.serialise_mapping_package import (serialise_mapping_package,
                                                                  serialise_mapping_package_to_folder,
                                                                  )
from mapping_suite_sdk.services.validate_mapping_package import (validate_mapping_package,
                                                                 validate_mapping_package_from_archive,
                                                                 validate_bulk_mapping_packages_from_folder,
                                                                 validate_bulk_mapping_packages_from_github)
from mapping_suite_sdk.vars import MSSDK_LOGGING_STRING_FORMAT, MSSDK_DATE_FORMAT

logging.basicConfig(level=logging.INFO,
                    format=MSSDK_LOGGING_STRING_FORMAT,
                    datefmt=MSSDK_DATE_FORMAT)

__version__ = importlib.metadata.version('mapping-suite-sdk')

__all__ = [
    ## Adapters
    # extractor.py
    "ArchivePackageExtractor",
    "GithubPackageExtractor",

    # hasher.py
    "MappingPackageHasher",

    # loader.py
    "TechnicalMappingSuiteLoader",
    "VocabularyMappingSuiteLoader",
    "TestDataSuitesLoader",
    "SPARQLTestSuitesLoader",
    "SHACLTestSuitesLoader",
    "MappingPackageMetadataLoader",
    "MappingPackageIndexLoader",
    "TestResultSuiteLoader",
    "ConceptualMappingFileLoader",
    "MappingPackageLoader",

    # repository.py
    "MongoDBRepository",

    # serialiser.py
    "TechnicalMappingSuiteSerialiser",
    "VocabularyMappingSuiteSerialiser",
    "TestDataSuitesSerialiser",
    "SPARQLTestSuitesSerialiser",
    "SHACLTestSuitesSerialiser",
    "MappingPackageMetadataSerialiser",
    "ConceptualMappingFileSerialiser",
    "MappingPackageSerialiser",

    # tracer.py
    "add_span_processor_to_mssdk_tracer_provider",
    "set_mssdk_tracing",
    "get_mssdk_tracing",

    # validator.py
    "MappingPackageValidator",

    ## Services
    # load_mapping_package.py
    "load_mapping_package_from_folder",
    "load_mapping_package_from_archive",
    "load_mapping_packages_from_github",
    "load_mapping_package_from_mongo_db",

    # serialise_mapping_package.py
    "serialise_mapping_package",
    "serialise_mapping_package_to_folder",

    # validate_mapping_package.py
    "validate_mapping_package",
    "validate_mapping_package_from_archive",
    "validate_bulk_mapping_packages_from_folder",
    "validate_bulk_mapping_packages_from_github",

    # Other
    "__version__"
]
