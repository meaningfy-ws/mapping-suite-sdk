import io, zipfile, sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from mapping_suite_sdk.core.models.file_asset import RMLMappingFileAsset

class MemPath(PurePosixPath):
    _files: dict = {}
    def is_file(self): return str(self) in self._files
    def is_dir(self): return any(k.startswith(str(self).rstrip("/") + "/") for k in self._files)
    def exists(self): return self.is_file() or self.is_dir()
    def iterdir(self):
        seen = set()
        for k in self._files:
            p = PurePosixPath(k)
            for anc in [p, *p.parents]:
                if anc.parent == self and anc != self and anc not in seen:
                    seen.add(anc); yield type(self)(anc)
    def read_bytes(self): return self._files[str(self)]
    def read_text(self, encoding="utf-8"): return self.read_bytes().decode(encoding)
    def relative_to(self, other): return Path(PurePosixPath(self).relative_to(other))

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr("pkg/transformation/mappings/a.rml.ttl", "x")
z = zipfile.ZipFile(buf)
cls = type("P", (MemPath,), {"_files": {"/" + n: z.read(n) for n in z.namelist() if not n.endswith("/")}})
root = cls("/pkg")
d = root / "transformation" / "mappings"
print(type(d).__name__, d.is_dir(), [str(c) for c in d.iterdir()])
f = next(d.iterdir())
print(RMLMappingFileAsset(path=f.relative_to(root), content=f.read_text()))
print(sys.version)
