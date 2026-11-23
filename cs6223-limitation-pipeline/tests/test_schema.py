import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schema.models import ALL_MODELS, Region

DATA = Path(__file__).resolve().parents[1] / "data"


def _records(path: Path):
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    if "_note" in data:
        return [r for v in data.values() if isinstance(v, list) for r in v]
    return [data]


# Limitset inputs and evaluator material have their own formats.
# pipeline.json is run config (written by `pipeline init --package-root`).
PROJECT_RECORDS = sorted(path for directory in DATA.iterdir() if directory.name != "limitset"
                         for path in directory.rglob("*.json") if path.name != "pipeline.json")


@pytest.mark.parametrize("path", PROJECT_RECORDS, ids=lambda p: p.name)
def test_every_data_file_is_schema_valid(path):
    for rec in _records(path):
        errors = []
        for model in ALL_MODELS.values():
            try:
                model.model_validate(rec)
                break
            except ValidationError as e:
                errors.append(e)
        else:
            pytest.fail(f"{path.name}: no model accepts {str(rec)[:100]}")


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        Region.model_validate({"region_id": "x", "unknown_field": 1})


def test_cross_references_resolve():
    pilot = DATA / "pilot_flexprefill"
    regions = {r["region_id"] for r in json.loads((pilot / "gold_regions.json").read_text())}
    lims = json.loads((pilot / "gold_code_limitations.json").read_text())
    assert all(set(l["region_ids"]) <= regions for l in lims)
    lim_ids = {l["limitation_id"] for l in lims}
    verifs = json.loads((pilot / "draft_verifications_3b.json").read_text())
    assert all(v["limitation_id"] in lim_ids for v in verifs)
    ver_ids = {v["verification_id"] for v in verifs}
    for f in json.loads((pilot / "draft_findings.json").read_text()):
        assert set(f["limitation_ids"]) <= lim_ids and set(f["verification_ids"]) <= ver_ids
