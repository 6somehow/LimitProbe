"""Mutation checks exercise published data integrity rather than model judgments."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from publish_handoff import publish
from validate_delivery import validate
from paperprobe.io import file_sha256


class HandoffPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = ROOT / 'handoffs/paper-side-v1/sparta'
        self.output = self.root / 'published'

    def package(self):
        publish(self.source, self.output)
        return self.output

    def edit(self, filename, change):
        path = self.output / filename
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        if filename == 'source-distribution.json':
            return
        # Refresh the distribution hash to reach the deeper semantic-independent invariant.
        distribution = self.output / 'source-distribution.json'
        record = json.loads(distribution.read_text())
        record['included'][filename] = file_sha256(path)
        distribution.write_text(json.dumps(record) + '\n')

    def test_published_existing_snapshots_pass_with_no_preexisting_distribution(self):
        for name in ['sparta', 'flexprefill']:
            source = self.root / f'source-{name}'
            source.mkdir()
            import shutil
            for path in (ROOT / 'handoffs/paper-side-v1' / name).iterdir():
                if path.is_file() and path.name != 'source-distribution.json':
                    shutil.copy2(path, source / path.name)
            (source / 'evidence').mkdir()
            (source / 'evidence' / 'paper.pdf').write_bytes(b'%PDF-local')
            for forbidden in ['audit.html', 'archive.zip', '.env', 'raw-response.json']:
                (source / forbidden).write_text('Do not distribute')
            destination = self.root / f'out-{name}'
            record = publish(source, destination)
            self.assertTrue(record['original_bundle_index_available'])
            for forbidden in ['evidence', 'audit.html', 'archive.zip', '.env', 'raw-response.json', 'bundle-index.json']:
                self.assertFalse((destination / forbidden).exists())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate(destination)['artifact_id'], name)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                publish(source, destination)

    def test_tampered_hash_is_rejected(self):
        self.package()
        path = self.output / 'paper_side.json'
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(AssertionError, 'Changed snapshot'):
            validate(self.output)

    def test_missing_behavior_is_rejected_even_after_counts_are_updated(self):
        self.package()
        self.edit('conformance.json', lambda rows: rows.pop(0))
        def update(proof):
            proof['conformance_rows'] -= 1
            proof['completed_artifact'] -= 1
        self.edit('validation.json', update)
        with self.assertRaisesRegex(AssertionError, 'Missing behavior for active claim'):
            validate(self.output)

    def test_missing_claim_reference_is_rejected(self):
        self.package()
        self.edit('conformance.json', lambda rows: rows[0].update(claim_id='sparta:missing'))
        with self.assertRaisesRegex(AssertionError, 'Missing claim reference'):
            validate(self.output)

    def test_unsupported_verdict_is_rejected(self):
        self.package()
        self.edit('conformance.json', lambda rows: rows[0]['artifact'].update(verdict='verified'))
        with self.assertRaisesRegex(AssertionError, 'Unsupported verdict'):
            validate(self.output)

    def test_pending_cannot_carry_a_conclusion(self):
        self.package()
        def change(rows):
            next(r for r in rows if r['artifact']['review_state'] == 'pending')['artifact']['verdict'] = 'absent'
        self.edit('conformance.json', change)
        with self.assertRaisesRegex(AssertionError, 'Pending verdict must be null'):
            validate(self.output)

    def test_missing_source_reference_is_rejected(self):
        self.package()
        def change(rows):
            row = rows[0]
            row['artifact']['refs'] = ['missing']
            row['evidence_registry_ids']['artifact'] = [row['mechanism_id'] + ':missing']
        self.edit('conformance.json', change)
        with self.assertRaisesRegex(AssertionError, 'Missing evidence reference'):
            validate(self.output)

    def test_original_quote_can_be_checked_when_numbered_paper_is_supplied(self):
        self.package()
        with self.assertRaisesRegex(AssertionError, 'Paper quote absent'):
            validate(self.output, defaultdict(str))

    def test_publisher_rejects_credential_content_without_leaving_output(self):
        import shutil
        source = self.root / 'source'
        shutil.copytree(self.source, source)
        (source / 'README.md').write_text('api_key = "' + 'testplaceholder' * 3 + '"')
        with self.assertRaisesRegex(ValueError, 'credential-like'):
            publish(source, self.output)
        self.assertFalse(self.output.exists())

    def test_frozen_behavior_ids_are_checked_and_exported(self):
        import shutil
        source = self.root / 'source'
        shutil.copytree(self.source, source)
        rows = json.loads((source / 'conformance.json').read_text())
        behaviors = {'behaviors': [{'id': row['id'], 'behavior': 'Original frozen behavior'} for row in rows]}
        mechanisms = {'mechanisms': [{'id': mid} for mid in sorted({r['mechanism_id'] for r in rows})]}
        (source / 'frozen-behaviors.json').write_text(json.dumps(behaviors))
        (source / 'mechanisms.json').write_text(json.dumps(mechanisms))
        publish(source, self.output)
        with contextlib.redirect_stdout(io.StringIO()):
            validate(self.output)
        self.edit('frozen-behaviors.json', lambda value: value['behaviors'].pop())
        with self.assertRaisesRegex(AssertionError, 'Frozen behavior IDs differ'):
            validate(self.output)

    def test_observation_counts_and_inactive_boundary(self):
        self.package()
        row = json.loads((self.output / 'paper_side.json').read_text())['eval_points'][0]
        original_id = row['eval_id']
        row['eval_id'] = 'held-observation'
        path = self.output / 'reported_observations.json'
        path.write_text(json.dumps([{'original_id': 'held', 'records': [row]}]))
        self.edit('source-distribution.json', lambda record: record['included'].update({'reported_observations.json': file_sha256(path)}))
        self.edit('validation.json', lambda proof: proof.update(reported_observation_groups=1, reported_observation_records=1))
        with contextlib.redirect_stdout(io.StringIO()):
            validate(self.output)
        self.edit('reported_observations.json', lambda groups: groups[0]['records'][0].update(eval_id=original_id))
        with self.assertRaisesRegex(AssertionError, 'Observation leaked'):
            validate(self.output)

    def test_missing_paper_backed_negative_limitation_is_rejected(self):
        self.package()
        self.edit('limitations.json', lambda rows: rows.pop())
        with self.assertRaisesRegex(AssertionError, 'Limitations differ'):
            validate(self.output)

    def test_distribution_cannot_escape_package(self):
        self.package()
        self.edit('source-distribution.json', lambda record: record['included'].update({'../outside': '0' * 64}))
        with self.assertRaises(AssertionError):
            validate(self.output)
