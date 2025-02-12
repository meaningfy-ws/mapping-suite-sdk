from pathlib import Path

from mssdk.core.adapters.importer import PackageImportProtocol
from mssdk.core.models.files import ConceptualMappingFile

RELATIVE_CONCEPTUAL_MAPPING_PATH = Path("transformation/conceptual_mappings.xlsx")


class ConceptualMappingFileImporter(PackageImportProtocol):

    def extract(self, package_path: Path) -> ConceptualMappingFile:
        cm_file_path: Path = package_path / RELATIVE_CONCEPTUAL_MAPPING_PATH

        return ConceptualMappingFile(
            path=RELATIVE_CONCEPTUAL_MAPPING_PATH,
            content=cm_file_path.read_bytes()
        )
