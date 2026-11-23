"""Quote-grounded, cached enrichment of mapped limitset findings."""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

PROMPT_VERSION = 'enrich-v1'
CATEGORIES = {
    'applicability_limitation': 'where or when the method does not apply (scope, assumptions, settings)',
    'mechanism_origin_unclear': 'the paper observes an effect or limit whose cause is not explained',
    'method_shortcoming': 'a weakness of the method itself (cost, accuracy loss, design flaw, missing handling)',
    'unclassified': 'none of the above',
}
_LOCK = threading.Lock()


class RelayLLM:
    def __init__(self, model, port):
        self.model = model
        self.port = port

    def __call__(self, prompt):
        from openai import OpenAI
        client = OpenAI(base_url=f'http://127.0.0.1:{self.port}/v1', api_key='relay', timeout=60, max_retries=0)
        response = client.chat.completions.create(
            model=self.model, temperature=0, response_format={'type': 'json_object'},
            messages=[{'role': 'user', 'content': prompt}])
        return response.choices[0].message.content


class FakeLLM:
    """Offline callable for tests and local integration checks."""
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, prompt):
        self.calls.append(prompt)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def enrich(finding, cache_dir, llm, model):
    """Return (finding, error); failures retain all original values."""
    payload = {'claim': finding['claim'], 'quotes': [e['support_description'] for e in finding['evidence'] if e.get('support_description')], 'category_definitions': CATEGORIES}
    prompt = ('Classify this finding using only the supplied claim and quotes. Return strict JSON '
              'with exactly category_code, mechanism, conditions. mechanism must be 1-2 sentences '
              'explaining why the limit arises, grounded in quotes; say "not stated" if absent. '
              'conditions must be a list of short strings describing when it occurs or applies.\n'
              + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    key = hashlib.sha256(json.dumps({'prompt': prompt, 'version': PROMPT_VERSION, 'model': model}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    path = Path(cache_dir) / (key + '.json')
    try:
        # Serialize cache misses so concurrent repeats cannot make duplicate calls.
        with _LOCK:
            result = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else json.loads(llm(prompt))
            if (not isinstance(result, dict) or set(result) != {'category_code', 'mechanism', 'conditions'}
                    or result['category_code'] not in CATEGORIES
                    or not isinstance(result['mechanism'], str) or not result['mechanism'].strip()
                    or not isinstance(result['conditions'], list)
                    or not all(isinstance(x, str) and x.strip() for x in result['conditions'])):
                raise ValueError('invalid enrichment response')
            if not path.is_file():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(result, ensure_ascii=False) + '\n', encoding='utf-8')
        return {**finding, **result}, None
    except Exception as exc:
        return finding, f'{type(exc).__name__}: {exc}'
