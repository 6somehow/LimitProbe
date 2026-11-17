import contextlib
import io
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

from paperprobe.io import read_json, file_sha256
from paperprobe.delivery import TEAM
from paperprobe.schema_contract import check_schema_snapshot

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from adapt_schema02 import checked_mapping
from validate_delivery import validate
from codeside.verify3b import load_paper_side
from codeside.scope_check import ScopeChecker
from codeside.witness import solve
from schema.models import Condition


class Schema02HandoffTests(unittest.TestCase):
    def test_strict_consumer_gate_does_not_hide_known_failures(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/validate_delivery.py'),
                                 '--root', str(ROOT/'handoffs/paper-side-v2'), '--strict-consumer'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 4)
        self.assertIn('known upstream failures', result.stdout)

    def test_two_migrated_packages_replay_consumer_contracts(self):
        for aid in ['flexprefill', 'nnsmith']:
            with self.subTest(aid=aid), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate(ROOT/'handoffs/paper-side-v2'/aid)['artifact_id'], aid)

    def test_consumer_bounds_come_from_paper_not_navigation(self):
        folder = ROOT/'handoffs/paper-side-v2/nnsmith'
        checker = ScopeChecker(*load_paper_side(str(folder/'paper_side.json')))
        allowed = solve(Condition(expr='kernel_w_size == 2', params=['kernel_w_size'], path_prefix=['kernel_w_size in {0, 1, 2, 3}']), checker)
        self.assertEqual(allowed['status'], 'solved')
        self.assertIn('pool2d_kernel_width', allowed['from_paper']['kernel_w_size'])
        self.assertEqual(checker.check(Condition(expr='kernel_w_size == 0')).scope_status, 'out_of_scope')
        self.assertEqual(solve(Condition(expr='kernel_w_size == 0'), checker)['status'], 'infeasible')
        self.assertTrue(all(b['kind'] == 'parameter' for b in read_json(folder/'paper_side.json')['bindings'] if b['code_symbol'] in checker.by_symbol))

    def test_decimal_equality_issue_is_not_recorded_as_a_passing_probe(self):
        folder = ROOT/'handoffs/paper-side-v2/flexprefill'
        equality = next(c for c in read_json(folder/'consumer_cases.json')['cases'] if c['input']['expr'] == 'tau == 0.1')
        # A fixed upstream solver may legitimately make this case pass on a future rebuild.
        self.assertEqual(equality['passed'], equality['witness']['status'] == equality['expected_witness'])
        if not equality['passed']:
            self.assertTrue(equality['known_upstream_failure'])
            self.assertEqual(equality['scope_result']['scope_status'], 'in_scope')

    def test_legacy_compatibility_does_not_accept_changed_paper_fields(self):
        original = ROOT/'handoffs/paper-side-v1/sparta/consumer_schema.snapshot.py'
        current = (TEAM/'schema/models.py').read_text()
        with tempfile.TemporaryDirectory() as temp:
            altered = Path(temp)/'schema.py'
            altered.write_text(current.replace('class Binding(_Record):', 'class Binding(_Record):\n    invented_field: int = 0'))
            with self.assertRaisesRegex(AssertionError, 'definitions changed'):
                check_schema_snapshot(original, altered, file_sha256(original))

    def test_migration_preserves_conformance_and_claim_statements(self):
        for aid in ['flexprefill', 'nnsmith']:
            old = ROOT/'handoffs/paper-side-v1'/aid
            new = ROOT/'handoffs/paper-side-v2'/aid
            self.assertEqual(file_sha256(old/'conformance.json'), file_sha256(new/'conformance.json'))
            a = [(c['claim_id'], c['statement'], c['evidence']) for c in read_json(old/'paper_side.json')['claims']]
            b = [(c['claim_id'], c['statement'], c['evidence']) for c in read_json(new/'paper_side.json')['claims']]
            self.assertEqual(a, b)

    def test_similar_names_without_formal_parameter_are_rejected(self):
        spec = dict(function='Pool.__init__', parameter='kernel_width', type='integer')
        code = 'class Pool:\n    def __init__(self, shape: list):\n        self.kernel_width = len(shape)\n'
        with self.assertRaises(StopIteration):
            checked_mapping(spec, code, [], 'a'*40)

    def test_declared_parameter_without_actual_storage_is_rejected(self):
        spec = dict(function='Pool.__init__', parameter='kernel_width', type='integer', path='pool.py',
                    source_checks=[dict(function='Pool.__init__', expression='self.kernel_width = kernel_width')])
        code = 'class Pool:\n    def __init__(self, kernel_width: int):\n        self.kernel_width = 1\n'
        with self.assertRaisesRegex(AssertionError, 'source step changed'):
            checked_mapping(spec, code, [], 'a'*40)
