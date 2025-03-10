# mapping-suite-sdk

![pylint](https://img.shields.io/badge/PyLint-8.62-yellow?logo=python&logoColor=white)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=bugs)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=coverage)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=meaningfy-ws_mapping-suite-sdk&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=meaningfy-ws_mapping-suite-sdk)

The Mapping Suite SDK, or MSSDK, is a software development kit (SDK) designed to standardize 
and simplify the handling of packages that contain transformation rules and related artefacts
for mapping data from XML to RDF (RDF Mapping Language).

## Quick Start

Install the SDK using pip:
```bash
pip install mapping-suite-sdk
```

or using poetry:
```bash
poetry add mapping-suite-sdk
```

### Loading a Mapping Package

The SDK provides several ways to load mapping packages:

```python
from pathlib import Path
import mapping_suite_sdk as mssdk 

# Load from a local folder
package = mssdk.load_mapping_package_from_folder(
    mapping_package_folder_path=Path("/path/to/mapping/package")
)

# Load from a ZIP archive
package = mssdk.load_mapping_package_from_archive(
    mapping_package_archive_path=Path("/path/to/package.zip")
)

# Load from GitHub
packages = mssdk.load_mapping_packages_from_github(
    github_repository_url="https://github.com/your-org/mapping-repo",
    packages_path_pattern="mappings/package*",
    branch_or_tag_name="main"
)
```

### Serializing a Mapping Package

```python
# Serialize a mapping package to a dictionary
package_dict = mssdk.serialise_mapping_package(mapping_package)
```

## Extractors

The SDK provides flexible extractors for working with mapping packages from different sources.

### Archive Package Extractor

Extract mapping packages from ZIP archives:

```python
from pathlib import Path
from mapping_suite_sdk import ArchivePackageExtractor

extractor = ArchivePackageExtractor()

# Extract to a specific location
output_path = extractor.extract(
    source_path=Path("package.zip"),
    destination_path=Path("output_directory")
)

# Extract to a temporary location (automatically cleaned up)
with extractor.extract_temporary(Path("package.zip")) as temp_path:
    # Work with files in temp_path
    pass  # Cleanup is automatic
```

### GitHub Package Extractor

Clone and extract mapping packages directly from GitHub repositories:

```python
from mapping_suite_sdk import GithubPackageExtractor

extractor = GithubPackageExtractor()

# Extract multiple packages matching a pattern
with extractor.extract_temporary(
    repository_url="https://github.com/org/repo",
    packages_path_pattern="mappings/package*",
    branch_or_tag_name="v1.0.0"
) as package_paths:
    for path in package_paths:
        # Process each package
        print(f"Found package at: {path}")
```

## MongoDB Support

The SDK provides seamless integration with MongoDB for storing and retrieving mapping packages.

### Setting Up the Repository

```python
from pymongo import MongoClient
from mapping_suite_sdk import MongoDBRepository
from mapping_suite_sdk.models.mapping_package import MappingPackage

# Initialize MongoDB client
mongo_client = MongoClient("mongodb://localhost:27017/")

# Create a repository for mapping packages
repository = MongoDBRepository(
    model_class=MappingPackage,
    mongo_client=mongo_client,
    database_name="mapping_suites",
    collection_name="packages"
)
```

### Loading and Storing Packages

```python
from pathlib import Path
from mapping_suite_sdk import load_mapping_package_from_folder, load_mapping_package_from_mongo_db

# Load a package from a folder
package = load_mapping_package_from_folder(
    mapping_package_folder_path=Path("/path/to/package")
)

# Store the package in MongoDB
repository.create(package)

# Retrieve the package by ID
retrieved_package = load_mapping_package_from_mongo_db(
    mapping_package_id=package.id,
    mapping_package_repository=repository
)

# Query multiple packages
packages = repository.read_many({"metadata.version": "1.0.0"})
```

## OpenTelemetry Tracing

The SDK includes built-in support for OpenTelemetry tracing, which helps with performance monitoring and debugging.

### Enabling Tracing

```python
from mapping_suite_sdk import set_mssdk_tracing, get_mssdk_tracing

# Enable tracing
set_mssdk_tracing(True)

# Check if tracing is enabled
is_enabled = get_mssdk_tracing()
```

### Adding Custom Span Processors

```python
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from mapping_suite_sdk import add_span_processor_to_mssdk_tracer_provider

# Add a console exporter for tracing output
console_exporter = ConsoleSpanExporter()
span_processor = SimpleSpanProcessor(console_exporter)
add_span_processor_to_mssdk_tracer_provider(span_processor)
```

### Using Tracer with OTLP Exporter

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from mapping_suite_sdk import add_span_processor_to_mssdk_tracer_provider, set_mssdk_tracing

# Configure and enable OpenTelemetry with OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
add_span_processor_to_mssdk_tracer_provider(span_processor)
set_mssdk_tracing(True)

# Now all SDK operations will be traced and sent to your collector
```

## Contributing

Contributions to the Mapping Suite SDK are welcome! Use fork and pull request workflow.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/meaningfy-ws/mapping-suite-sdk.git
cd mapping-suite-sdk

# Install dependencies
# Use Makefile commands
make install

# Run tests
make test-unit
```

## Get in Touch

- **Issues**: Report bugs and feature requests on our [GitHub Issues](https://github.com/meaningfy-ws/mapping-suite-sdk/issues)
- **Email**: Contact the team at [hi@meaningfy.ws](mailto:hi@meaningfy.ws)
- **Website**: Visit our website at [meaningfy.ws](https://meaningfy.ws)

## References

- [Mapping Package Structure Documentation](http://docs.ted.europa.eu/ODS/latest/mapping_eforms/package_structure.html#_the_eforms_metadata_json_file)
- [TED RDF Conversion Pipeline](https://github.com/OP-TED/ted-rdf-conversion-pipeline)