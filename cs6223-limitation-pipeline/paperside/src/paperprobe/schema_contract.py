"""Check legacy paper-interface compatibility without executing archived schema code."""
import ast
from pathlib import Path
from .io import file_sha256


def _parts(source):
    tree = ast.parse(source)
    classes = {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.ClassDef)}
    version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'SCHEMA_VERSION' for t in n.targets))
    return version, classes


def check_schema_snapshot(snapshot: Path, current: Path, expected_hash: str):
    assert file_sha256(snapshot) == expected_hash, 'Archived consumer schema changed'
    if file_sha256(current) == expected_hash:
        return 'exact schema snapshot'
    old_version, old = _parts(snapshot.read_text())
    new_version, new = _parts(current.read_text())
    assert (old_version, new_version) == ('0.1.0', '0.2.0'), 'Unreviewed schema version transition'
    # Includes all classes used transitively by the paper-side shared records. Findings
    # are explicitly excluded: they belong to step 4, and DID change in 0.2.0.
    required = [name for name in old if name not in {'FindingCategory', 'Finding', 'ReviewStatus'}]
    assert all(old[name] == new.get(name) for name in required), 'Shared paper record definitions changed'
    return 'legacy 0.1.0 records structurally compatible with 0.2.0; historical files not migrated'
