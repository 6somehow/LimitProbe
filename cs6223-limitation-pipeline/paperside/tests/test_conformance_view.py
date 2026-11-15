import unittest
from copy import deepcopy
from paperprobe.conformance_view import three_conclusion_view

class ConformanceViewTests(unittest.TestCase):
    def test_three_conclusions_do_not_change_completed_verdicts_or_original(self):
        original={'checks':[{'id':'B1','claim_type':'mechanism_step','local_entry':{'verdict':'absent','barrier':''},'artifact':{'verdict':'deviates','barrier':''}}]}
        before=deepcopy(original);view=three_conclusion_view(original)
        self.assertEqual(original,before)
        for scope in ['local_entry','artifact']:
            self.assertEqual(view['checks'][0][scope]['verdict'],original['checks'][0][scope]['verdict'])
            self.assertEqual(view['checks'][0][scope]['review_state'],'completed')
    def test_pending_is_work_state_with_no_semantic_verdict(self):
        original={'checks':[{'id':'B8','claim_type':'guarantee','local_entry':{'verdict':'insufficient','barrier':'not assessed'},'artifact':{'verdict':'insufficient','barrier':'not assessed'}}]}
        view=three_conclusion_view(original)
        for scope in ['local_entry','artifact']:
            v=view['checks'][0][scope]
            self.assertIsNone(v['verdict']);self.assertEqual(v['review_state'],'pending')
            self.assertTrue(v['pending_reason']);self.assertEqual(v['legacy_assessment']['verdict'],'insufficient')
        self.assertEqual(view['status_migration']['new_model_requests'],0)
    def test_existing_lifecycle_is_not_rejudged(self):
        original={'checks':[{'id':'B','claim_type':'guarantee','local_entry':{'review_state':'completed','verdict':'supports'},'artifact':{'review_state':'pending','verdict':None}}]}
        view=three_conclusion_view(original)
        self.assertEqual(view['checks'],original['checks'])
