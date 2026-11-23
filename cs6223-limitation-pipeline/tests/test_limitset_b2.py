import json
import os
from pathlib import Path

import pytest

from limitset_baselines import b2


def test_json_adapter():
    findings, errors = b2._parse(json.dumps([{'claim': 'Limited scale', 'evidence': [{'source_id': 'paper', 'location': 'p. 2', 'support_description': 'quote'}]}]))
    assert not errors
    assert findings[0]['category_code'] == 'unclassified'
    assert findings[0]['evidence'][0]['support_description'] == 'quote'
    assert findings[0]['conditions'] == []
    assert 'confidence' not in findings[0]


def test_free_text_and_bad_evidence():
    findings, errors = b2._parse('- First limitation\n2. Second limitation')
    assert [x['claim'] for x in findings] == ['First limitation', 'Second limitation']
    assert errors
    assert b2._parse('No structured output')[1]
    assert b2._parse('[{"claim":"x", "evidence":["quote"]}]')[1]


def test_run_fake_opencode(tmp_path, monkeypatch):
    source = tmp_path / 'input'
    source.mkdir()
    (source / 'paper.pdf').write_bytes(b'pdf')
    (source / 'paper.txt').write_text('paper')
    (source / 'labels').mkdir()
    (source / 'labels' / 'secret.txt').write_text('secret')
    fake = tmp_path / 'opencode'
    fake.write_text('#!/bin/sh\nprintf \'%s\\n\' \'{"type":"text","part":{"text":"[{\\"claim\\":\\"A\\"}]"}}\' \'{"type":"step_finish","part":{"tokens":{"input":4,"output":2}}}\'\n')
    fake.chmod(0o755)
    wrapper = tmp_path / 'bwrap'
    wrapper.write_text('#!/bin/sh\nwhile [ "$1" != "--chdir" ]; do shift; done\nshift\ncd "$1"\nshift\nexec "$@"\n')
    wrapper.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ.get('PATH', ''))
    monkeypatch.setattr(b2, 'HOME_TEMPLATE', tmp_path / 'missing')
    result = b2.run_case('CS6223-12', source, tmp_path / 'out', {'LIMITSET_OPENCODE': str(fake)}, 1)
    assert result['findings'][0]['claim'] == 'A'
    assert result['cost']['prompt_tokens'] == 4
    assert result['cost']['turns'] == 1
    assert not (tmp_path / 'out/workspace/labels').exists()
    with pytest.raises(FileExistsError):
        b2.run_case('CS6223-12', source, tmp_path / 'out', {'LIMITSET_OPENCODE': str(fake)}, 1)


def test_timeout_kills_process_group(tmp_path, monkeypatch):
    source = tmp_path / 'input'
    source.mkdir()
    (source / 'paper.pdf').write_bytes(b'pdf')
    (source / 'paper.txt').write_text('paper')
    fake = tmp_path / 'opencode'
    fake.write_text('#!/bin/sh\nsleep 30 &\nwait\n')
    fake.chmod(0o755)
    wrapper = tmp_path / 'bwrap'
    wrapper.write_text('#!/bin/sh\nwhile [ "$1" != "--chdir" ]; do shift; done\nshift\ncd "$1"\nshift\nexec "$@"\n')
    wrapper.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ.get('PATH', ''))
    monkeypatch.setattr(b2, 'HOME_TEMPLATE', tmp_path / 'missing')
    result = b2.run_case('CS6223-01', source, tmp_path / 'out',
                         {'LIMITSET_OPENCODE': str(fake), 'LIMITSET_OPENCODE_TIMEOUT': '0.1'}, 0)
    assert 'opencode timed out' in result['parse_failures']
    assert result['wall_seconds'] < 5 if 'wall_seconds' in result else result['cost']['wall_seconds'] < 5
