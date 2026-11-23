import json
import re
from pathlib import Path

import pytest

from checklimits.checklimits.paper_only import V3_INVENTORY, V3_SWEEP, V3_WRITE, V3_FILTER


def test_v3_prompt_has_no_label_ngrams():
    english = Path('data/limitset/labels_en.jsonl')
    chinese = Path('<limitset-raw>/labels/test_labels.jsonl')
    if not english.is_file() or not chinese.is_file():
        pytest.skip('scorer labels unavailable')
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from strings(v)
        elif isinstance(value, list):
            for v in value:
                yield from strings(v)
    prompts = ' '.join([V3_INVENTORY.format(text='', code=''), V3_SWEEP.format(inventory='', text='', code=''),
                        V3_WRITE.format(sweep='', inventory='', text='', code=''), V3_FILTER.format(candidates='')]).lower()
    words = re.findall(r'\w+', prompts)
    prompt_grams = set(zip(*(words[i:] for i in range(5))))
    for line in english.read_text(encoding='utf-8').splitlines():
        for value in strings(json.loads(line)):
            tokens = re.findall(r'\w+', value.lower())
            assert not (set(zip(*(tokens[i:] for i in range(5)))) & prompt_grams)
    for line in chinese.read_text(encoding='utf-8').splitlines():
        for value in strings(json.loads(line)):
            chars = ''.join(re.findall(r'[\u4e00-\u9fff]', value))
            assert all(chars[i:i + 8] not in prompts for i in range(len(chars) - 7))
