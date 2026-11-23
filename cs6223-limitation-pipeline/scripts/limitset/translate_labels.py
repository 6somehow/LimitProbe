"""Translate scorer-only reference labels through the local relay."""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scorer_limitset.scoring import RelayJudge, read_jsonl

PROMPT_VERSION = "translate-labels-v1"
TEMPERATURE = 0.0


def translate_labels(labels, out, translator, model_id):
    """Cache translations by source content and translator configuration."""
    out = Path(out)
    manifest_path = out.with_suffix('.manifest.json')
    config = {"model_id": model_id, "prompt_version": PROMPT_VERSION, "temperature": TEMPERATURE}
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    cache = manifest.get('cache', {}) if all(manifest.get(k) == v for k, v in config.items()) else {}
    translated = []
    for label in labels:
        digest = hashlib.sha256(json.dumps(label, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if digest not in cache:
            result = translator(label)
            validate_translation(label, result)
            cache[digest] = result
        validate_translation(label, cache[digest])
        translated.append(cache[digest])
        out.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({**config, 'cache': cache}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in translated), encoding='utf-8')
    manifest_path.write_text(json.dumps({**config, 'cache': cache}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_translation(source, result):
    if isinstance(source, dict):
        if not isinstance(result, dict) or source.keys() != result.keys():
            raise ValueError('translation changed object structure')
        for key in source:
            validate_translation(source[key], result[key])
    elif isinstance(source, list):
        if not isinstance(result, list) or len(source) != len(result):
            raise ValueError('translation changed array structure')
        for a, b in zip(source, result):
            validate_translation(a, b)
    elif isinstance(source, str):
        if not isinstance(result, str):
            raise ValueError('translation changed string type')
        # Non-Chinese values include IDs, category codes, paths and identifiers.
        if not any('\u4e00' <= c <= '\u9fff' for c in source) and source != result:
            raise ValueError('translation changed a non-Chinese string')
    elif type(source) is not type(result) or source != result:
        raise ValueError('translation changed a non-text value')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--model', default='x-test-2')
    args = parser.parse_args()
    labels = read_jsonl(args.root / 'labels/test_labels.jsonl')
    from pipeline.e2e import RELAY_URL, PLACEHOLDER_KEY
    def translate(label):
        prompt = ('Translate Chinese text in this JSON reference to English. Preserve every key, array, '
                  'non-Chinese string, technical term, identifier and source location exactly. '
                  'Return only the complete JSON object.\n' + json.dumps(label, ensure_ascii=False))
        body = json.dumps({'model': args.model, 'temperature': TEMPERATURE,
                           'messages': [{'role': 'user', 'content': prompt}],
                           'response_format': {'type': 'json_object'}}).encode()
        request = urllib.request.Request(RELAY_URL + '/chat/completions', data=body,
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + PLACEHOLDER_KEY})
        import time, urllib.error
        for attempt in range(8):  # upstream rate limits (HTTP 429) are transient: back off and retry
            try:
                with urllib.request.urlopen(request, timeout=420) as response:
                    return json.loads(json.load(response)['choices'][0]['message']['content'])
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 7:
                    raise
                time.sleep(20 * (attempt + 1))
    with RelayJudge(args.root, args.model):
        translate_labels(labels, args.out, translate, args.model)


if __name__ == '__main__':
    main()
