"""Write one JSON Schema file per record type into schema/json/.

Usage: python -m schema.export_json_schema
Teammates who do not use Python can validate their output against these files.
"""

import json
from pathlib import Path

from schema.models import ALL_MODELS, SCHEMA_VERSION

OUT = Path(__file__).parent / "json"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, model in ALL_MODELS.items():
        path = OUT / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {path}")
    print(f"schema version {SCHEMA_VERSION}")


if __name__ == "__main__":
    main()
