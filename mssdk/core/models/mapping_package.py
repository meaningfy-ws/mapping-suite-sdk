from typing import List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class XMLTestFile(BaseModel):

    name: str = Field(description="Name of the XML file")
    content: str = Field(description="Content of the XML file")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

class TestData(BaseModel):

    files: List[XMLTestFile] = Field(
        default_factory=list,
        description="Collection of XML test files"
    )

class ConceptualMapping(BaseModel):

    name: str = Field(description="Name of the conceptual mapping file")

    sheets: Dict[str, List[Dict[str, str]]] = Field(
        description="Excel sheets data where each sheet is represented as a list of rows"
    )

class TechnicalMapping(BaseModel):

    name: str = Field(description="Name of the TTL file")
    content: str = Field(description="Content of the TTL file")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

class TransformationData(BaseModel):

    conceptual_mapping: ConceptualMapping = Field(
        description="Conceptual mapping data from Excel"
    )
    technical_mappings: List[TechnicalMapping] = Field(
        default_factory=list,
        description="Collection of technical mapping TTL files"
    )

class SHACLShape(BaseModel):

    name: str = Field(description="Name of the SHACL shape file")
    content: str = Field(description="Content of the SHACL shape in TTL format")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

class SPARQLQuery(BaseModel):

    name: str = Field(description="Name of the SPARQL query file")
    content: str = Field(description="Content of the SPARQL query")
    description: str = Field(default="", description="Optional description of what the query validates")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

class ValidationData(BaseModel):

    shacl_shapes: List[SHACLShape] = Field(
        default_factory=list,
        description="Collection of SHACL shape files"
    )
    sparql_queries: List[SPARQLQuery] = Field(
        default_factory=list,
        description="Collection of SPARQL query files"
    )

class MappingPackage(BaseModel):

    package_name: str = Field(description="Name of the mapping package")
    package_version: str = Field(
        description="Version of the mapping package",
        pattern=r"^\d+\.\d+\.\d+$"  # Semantic versioning pattern
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Package creation timestamp"
    )
    description: str = Field(
        default="",
        description="Optional description of the mapping package"
    )
    test_data: TestData = Field(
        default_factory=TestData,
        description="Test data component of the package"
    )
    transformation_data: TransformationData = Field(
        description="Transformation data component of the package"
    )
    validation_data: ValidationData = Field(
        default_factory=ValidationData,
        description="Validation data component of the package"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }