"""Provider-independent immutable CSV bundles; all paths remain below the asset root."""
import json

from .files import safe_path, verify
from .providers import read_csv_series


def manifest(source, settings):
    path = safe_path(source.local.directory, source.local.manifest)
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("resource_id") != source.id or spec.get("version") != source.version:
        raise ValueError("资源清单编号或版本不匹配")
    return path.parent, spec


class ManifestCSVProvider:
    def __init__(self, source, settings):
        self.source, self.settings = source, settings

    def read(self, case, variable):
        root, spec = manifest(self.source, self.settings)
        safe_path(root, case.directory)
        safe_path(root, variable.file)
        relative = case.directory.rstrip("/") + "/" + variable.file if case.directory else variable.file
        path = safe_path(root, relative)
        expected = spec["files"][relative]
        verify(path, expected)
        return read_csv_series(path, variable,
            {"source_id": self.source.id, "dataset_id": self.source.id, "revision": self.source.version,
             "sha256": expected["sha256"], "license": self.source.license, "citation": self.source.citation,
             "asset_origin": "local"})
