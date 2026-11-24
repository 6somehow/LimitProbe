import json

import pytest

from pipeline import limitset


def test_dataset2_selection_and_schema(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    directory = root / 'data/limitset2'
    directory.mkdir(parents=True)
    (directory / 'cases.jsonl').write_text(json.dumps({'case_id': 'LS2-01'}) + '\n')
    raw = tmp_path / 'original'
    (raw / 'schemas').mkdir(parents=True)
    (raw / 'schemas/prediction.schema.json').write_text(json.dumps({
        'type': 'object', 'properties': {'case_id': {'type': 'string', 'pattern': '^CS6223-'}},
    }))
    monkeypatch.setattr(limitset, 'ROOT', root)
    monkeypatch.setattr(limitset, 'RAW', raw)
    path, cases, ids = limitset.dataset_cases('limitset2', 'test')
    assert path == directory / 'cases.jsonl'
    assert ids == ['LS2-01'] and cases[0]['case_id'] == ids[0]
    schema = limitset.dataset_schema('limitset2', tmp_path)
    limitset.validate({'case_id': 'LS2-01', 'findings': []}, schema)
    with pytest.raises(ValueError):
        limitset.dataset_cases('limitset2', 'validation')


def test_blindness_blocks_label_files_and_review(tmp_path):
    for name in ('labels.jsonl', 'REVIEW.md'):
        with pytest.raises(AssertionError):
            limitset.safe_path(tmp_path / name)


def test_heldout_label_prompt_leakage():
    import ast
    import re
    from pathlib import Path
    from checklimits.checklimits import paper_only

    root = Path(__file__).resolve().parents[1]
    labels = root / 'data/limitset2/labels.jsonl'
    if not labels.exists():
        pytest.skip('held-out labels are not available')
    def grams(text):
        words = re.findall(r'[a-z]+', text.lower())
        return set(zip(*(words[i:] for i in range(5))))
    prompt_names = ('MECH_TASK', 'MECH_INVENTORY', 'MECH_ANALYSIS',
                    'V3_INVENTORY', 'V3_SWEEP', 'V3_WRITE', 'V3_FILTER')
    prompts = [getattr(paper_only, name) for name in prompt_names]
    tree = ast.parse((root / 'limitset_baselines/b1.py').read_text())
    run_case = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run_case')
    assignment = next(node for node in run_case.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'prompt' for t in node.targets))
    prompts.append(' '.join(node.value for node in ast.walk(assignment.value) if isinstance(node, ast.Constant) and isinstance(node.value, str)))
    reference = grams(labels.read_text(encoding='utf-8'))
    for prompt in prompts:
        assert not reference.intersection(grams(prompt))
