import contextlib
from fractions import Fraction
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from paperprobe.io import read_json, write_json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_z3_handoff import prefix_reference
from validate_z3_handoff import validate


class Z3HandoffTests(unittest.TestCase):
    def package(self,aid):
        return ROOT/'handoffs/z3-v1'/aid
    def primary(self,aid):
        return next(h for h in read_json(self.package(aid)/'testability_hints.json')['hints'] if h.get('finding_id'))
    def test_both_source_backed_packages_are_readable_without_execution(self):
        for aid in ['flexprefill','nnsmith']:
            with self.subTest(aid=aid),contextlib.redirect_stdout(io.StringIO()):
                result=validate(self.package(aid))
                self.assertEqual(result['target_execution'],'not_run')
    def test_full_negative_inventory_is_retained_not_just_selected_examples(self):
        self.assertEqual(len(read_json(self.package('flexprefill')/'testability_hints.json')['hints']),21)
        self.assertEqual(len(read_json(self.package('nnsmith')/'testability_hints.json')['hints']),6)
    def test_reference_boundary_and_control_are_exact_rational_arithmetic(self):
        values=[Fraction(1,512)]*512
        self.assertEqual(prefix_reference(values,Fraction(127,512)),127)
        self.assertEqual(prefix_reference(values,Fraction(127,512),True),128)
        self.assertEqual(prefix_reference(values,Fraction(255,1024)),128)
        self.assertEqual(prefix_reference(values,Fraction(255,1024),True),128)
    def test_flex_does_not_hide_ambiguity_or_claim_helper_input_reaches_public_entry(self):
        p=self.primary('flexprefill')
        self.assertTrue(any('exceeds' in b for b in p['blockers']))
        self.assertTrue(any('NOT solved' in b for b in p['blockers']))
        self.assertEqual(p['effect_type'],'other')
    def test_nn_timeout_units_and_zero_budget_outer_loop_barrier_are_explicit(self):
        p=self.primary('nnsmith')
        self.assertIn('timeout_ms/1000',p['call_chain'][1]['formal_parameter_map']['max_time'])
        self.assertTrue(any('skips its own loop' in b for b in p['path_conditions']))
        self.assertEqual(p['target']['snippet'].strip(),'return sat_inputs')
    def test_experiment_signature_mismatch_is_static_not_a_runtime_observation(self):
        p=self.primary('nnsmith')['experiment_route_check']
        self.assertEqual(p['unsupported_keywords'],['return_list'])
        self.assertIn('not executed',p['analysis'])
    def test_theory_and_hardware_claims_are_not_automatically_executable_requirements(self):
        hints=read_json(self.package('flexprefill')/'testability_hints.json')['hints']
        self.assertTrue(all(h['plan_state']=='needs_semantic_review' for h in hints if h['behavior'].startswith('M11-')))
        self.assertEqual(next(h for h in hints if h['behavior']=='M12-A05')['plan_state'],'needs_semantic_review')
    def test_possible_random_halving_equivalence_is_kept_for_review(self):
        h=next(h for h in read_json(self.package('nnsmith')/'testability_hints.json')['hints'] if h['behavior']=='M05-B08-R02')
        self.assertEqual(h['plan_state'],'needs_semantic_review')
        self.assertIn('distribution-equivalent',h['testability_note'])
    def test_paper_origin_is_preserved_even_when_native_adapter_skips_it(self):
        for aid in ['flexprefill','nnsmith']:
            native=read_json(self.package(aid)/'limitations_for_tests.json')['findings'][0]
            self.assertTrue(all(l['origin']=='paper' and l['code_evidence'] for l in native['limitations']))
            check=read_json(self.package(aid)/'consumer_contract_check.json')['checks'][0]
            self.assertGreater(check['paper_locations_supplied'],0)
            self.assertEqual(check['native_region_count'],0)
    def mutation(self,change):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'case';shutil.copytree(self.package('nnsmith'),folder)
            index=folder/'package-index.json'
            if index.exists():index.unlink()
            change(folder)
            with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(AssertionError):validate(folder)
    def test_missing_triage_is_rejected(self):
        def change(folder):
            p=folder/'testability_hints.json';d=read_json(p);d['hints'].pop();write_json(p,d)
        self.mutation(change)
    def test_false_reject_label_on_return_statement_is_rejected(self):
        def change(folder):
            p=folder/'limitations_for_tests.json';d=read_json(p);d['findings'][0]['effect_type']='reject';write_json(p,d)
        self.mutation(change)
    def test_fabricated_test_verdict_in_not_run_report_is_rejected(self):
        def change(folder):
            p=next((folder/'contract_output/tests/nnsmith').glob('*/report.json'));d=read_json(p);d['verdict']='yes';write_json(p,d)
        self.mutation(change)
    def test_changed_target_snippet_is_rejected(self):
        def change(folder):
            p=folder/'testability_hints.json';d=read_json(p);next(h for h in d['hints'] if h.get('finding_id'))['target']['snippet']='raise RuntimeError()';write_json(p,d)
        self.mutation(change)
