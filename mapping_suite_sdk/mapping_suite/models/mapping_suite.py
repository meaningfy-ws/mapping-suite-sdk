from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from mapping_suite_sdk.core.models.pydantic import PydanticModel

metamodel_version = "None"
version = "0.1.0"


class ExtractionMethod(str, Enum):
    """
    Enumeration of supported extraction methods for retrieving values from source documents.

    """

    text = "text"
    """
    Extract the text content of the located element
    """
    attribute = "attribute"
    """
    Extract a specific attribute value from the located element
    """
    attribute_and_text = "attribute_and_text"
    """
    Extract both an attribute value and the text content
    """
    element = "element"
    """
    Extract the entire element (e.g., for complex nested structures)
    """


class FormalExpressionType(str, Enum):
    """
    Enumeration of formal expression types supported for property extraction.

    """

    xpath = "xpath"
    """
    XPath expression for XML documents
    """
    xquery = "xquery"
    """
    XQuery expression for XML documents
    """
    jsonpath = "jsonpath"
    """
    JSONPath expression for JSON documents
    """


class MatchingMethod(str, Enum):
    """
    Enumeration of methods for matching metadata property values against package constraint properties.

    """

    in_list = "in_list"
    """
    Check if the metadata property value is in a list of allowed values (list membership).
    Used with document_type_list and similar list-based constraints.

    """
    equals = "equals"
    """
    Check for exact equality between metadata property value and constraint property value
    """
    range = "range"
    """
    Check if the metadata property value falls within a range (min/max).
    Used with version ranges and date intervals.

    """
    table_lookup = "table_lookup"
    """
    Look up the metadata property value in a normalization/mapping table.
    Used for Standard Forms where subtypes need to be mapped via a lookup table.

    """
    regex = "regex"
    """
    Match the metadata property value against a regular expression pattern
    """


class MappingSuite(PydanticModel):
    """
    Root container for a complete mapping suite.
    Encapsulates the core configuration and resources directory.

    """

    mapping_suite_config: MappingSuiteConfig = Field(
        default=...,
        description="""Core configuration for the mapping suite.
Contains metadata, probing rules, extraction specifications, and eligibility mappings.
Loaded from: mapping_suite_config.json
""",
    )
    resource_references: ResourceReferences = Field(
        default=...,
        description="""A list of references to resource files in the mapping suite (vocabulary resources, code lists, and other auxiliary files).      
""",
    )
    resource_file_contents: Optional[list[Any]] = Field(
        default=None,
        description="""List of laoded file objects, modelled elsewhere as FileAsset""",
    )


class MappingSuiteConfig(PydanticModel):
    """
    Core configuration for a mapping suite (project).
    Encapsulates the four components of a mapping suite configuration:
    suite metadata, document probing rules, extraction rules, and eligibility mappings.
    Serialized to: mapping_suite_config.json
    Properties are defined within the extraction configuration.

    """

    mapping_suite_metadata: MappingSuiteMetadata = Field(
        default=...,
        description="""Metadata describing the mapping suite itself.
Loaded from mapping_suite_metadata.json
""",
    )
    metadata_config: DocumentMetadataConfig = Field(
        default=...,
        description="""Configuration defining how to extract metadata properties from source documents.
Loaded from the fixed file: metadata_config.json
""",
    )
    eligibility_constraint_config: EligibilityConstraintConfig = Field(
        default=...,
        description="""Configuration mapping metadata properties to package eligibility constraints.
Loaded from the fixed file: eligibility_constraint_config.json
Used to select which mapping package applies to a given document.
""",
    )


class DocumentProbingSpec(PydanticModel):
    """
    Specification for probing if a document matches the signature of this mapping suite.
    Contains conditions that must exist and conditions that must not exist in the document.
    Used to determine if a document should be processed with this suite's configuration.

    """

    must_exist: Optional[list[PropertyExtractionSpec]] = Field(
        default=None,
        description="""List of extraction specifications that must successfully match in the document.
All must_exist conditions must be satisfied for the document to be eligible for this suite.
Examples: presence of eForms specific markers, required XML namespaces, etc.
""",
    )
    must_not_exist: Optional[list[PropertyExtractionSpec]] = Field(
        default=None,
        description="""List of extraction specifications that must NOT match in the document.
If any must_not_exist condition matches, the document is NOT eligible for this suite.
Examples: absence of Standard Forms markers, exclusion of specific XML elements, etc.
""",
    )


class MappingSuiteMetadata(PydanticModel):
    """
    Metadata describing the mapping suite itself.
    Contains identifier and description for the suite.

    """

    mapping_suite_identifier: str = Field(
        default=...,
        description="""Unique identifier for the mapping suite.
Used to identify and reference this suite in configurations and processing.
""",
    )
    mapping_suite_description: Optional[str] = Field(
        default=None,
        description="""Human-readable description of the mapping suite.
Explains the purpose and scope of this suite.
""",
    )


class DocumentMetadataConfig(PydanticModel):
    """
    Configuration for extracting metadata properties from source documents.
    Loaded from the fixed file: metadata_config.json
    Contains an array of property definitions with their XPath/XQuery/JSONPath extraction specifications.

    """

    metadata_properties: list[PropertyDefinition] = Field(
        default=...,
        description="""List of metadata property definitions to extract from documents""",
    )
    document_type_probing: Optional[DocumentProbingSpec] = Field(
        default=None,
        description="""Specification for probing if a document matches the signature of this mapping suite.
Used to determine if a document should be processed with this suite's configuration.
Optional; if not provided, the suite applies to all documents processed by this system.
""",
    )


class PropertyDefinition(PydanticModel):
    """
    Definition of a single metadata property to extract from source documents.
    Each property has an identifier and one or more extraction specifications
    that define how to locate and extract the value from the source.

    """

    property: str = Field(
        default=...,
        description="""Unique identifier for a metadata property.
In PropertyDefinition: the property being defined.
In PropertyEligibilityMapping: reference to the extracted property.
""",
    )
    property_extractors: list[PropertyExtractionSpec] = Field(
        default=...,
        description="""One or more extraction specifications for this property.
Multiple specifications are tried in order (fallback logic).
""",
    )
    property_description: Optional[str] = Field(
        default=None,
        description="""Human-readable description of what this property represents""",
    )


class PropertyExtractionSpec(PydanticModel):
    """
    Specification for extracting a metadata property value from a source document.
    Defines a formal expression (XPath, XQuery, or JSONPath), expression type, and extraction method.

    """

    formal_expression: str = Field(
        default=...,
        description="""Formal expression to locate and extract the value from a source document.
Can be an XPath expression (for XML), XQuery expression, or JSONPath expression (for JSON).
""",
    )
    formal_expression_type: FormalExpressionType = Field(
        default=...,
        description="""Type of the formal expression: XPath (for XML), XQuery, or JSONPath (for JSON).
""",
    )
    extraction_method: ExtractionMethod = Field(
        default=...,
        description="""Method used to extract the value from the located element.
""",
    )
    attribute_name: Optional[str] = Field(
        default=None,
        description="""Name of the XML/JSON attribute to extract when using attribute-based extraction methods.
Required when extraction_method is 'attribute' or 'attribute_and_text'.
""",
    )


class EligibilityConstraintConfig(PydanticModel):
    """
    Configuration for mapping extracted metadata properties to package eligibility constraints.
    Loaded from the fixed file: eligibility_constraint_config.json
    Defines which metadata properties are used to select the appropriate mapping package
    for a given document.

    """

    eligibility_mapping: list[PropertyEligibilityMapping] = Field(
        default=...,
        description="""List of metadata property to package constraint property mappings (at least one required)""",
    )


class PropertyEligibilityMapping(PydanticModel):
    """
    Maps a metadata property (extracted from the document) to a package constraint property.
    Specifies the matching method used to determine if a package is applicable.

    """

    property: str = Field(
        default=...,
        description="""Unique identifier for a metadata property.
In PropertyDefinition: the property being defined.
In PropertyEligibilityMapping: reference to the extracted property.
""",
    )
    constraint_property: str = Field(
        default=...,
        description="""Identifier of the constraint property in the mapping package eligibility_constraints.
This is the property in the package metadata that the extracted property will be matched against.
""",
    )
    matching_method: MatchingMethod = Field(
        default=...,
        description="""Method used to match the extracted property value against the constraint property.
""",
    )
    description: Optional[str] = Field(
        default=None,
        description="""Human-readable description of this eligibility mapping""",
    )


class ResourceReferences(PydanticModel):
    """
    Represents the list of relative path references to files containing vocabulary resources, code lists,
    normalization tables, and other auxiliary files needed for processing.

    """

    file_paths: Optional[list[str]] = Field(
        default=None, description="""List of relative file paths within the project"""
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
MappingSuite.model_rebuild()
MappingSuiteConfig.model_rebuild()
DocumentProbingSpec.model_rebuild()
MappingSuiteMetadata.model_rebuild()
DocumentMetadataConfig.model_rebuild()
PropertyDefinition.model_rebuild()
PropertyExtractionSpec.model_rebuild()
EligibilityConstraintConfig.model_rebuild()
PropertyEligibilityMapping.model_rebuild()
ResourceReferences.model_rebuild()
