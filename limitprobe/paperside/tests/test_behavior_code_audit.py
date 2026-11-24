import unittest

from paperprobe.behavior_code_audit import validate_result


class CodeAuditTest(unittest.TestCase):
    def setUp(self):
        self.row=dict(id='M02-B01',kind='mechanism')
        self.pool=dict(snippets={k:dict(complete=True) for k in ['S1','S2','S3']},
                       edges=dict(E1=dict(caller='S1',callee='S2')))

    def test_connected_support_is_retained_but_not_marked_human_validated(self):
        raw=dict(checks=[dict(id='M02-B01',result='supported',snippets=['S2'],edges=['E1'],
                             entry='S1',rationale='Entry calls the implementing body')])
        result=validate_result(raw,self.row,self.pool)
        self.assertEqual(result['result'],'supported')
        self.assertEqual(result['semantic_review'],'pending')

    def test_unconnected_partial_keeps_model_verdict_and_flags_evidence(self):
        raw=dict(checks=[dict(id='M02-B01',result='partial',snippets=['S3'],edges=['E1'],
                             entry='S1',rationale='Separate helper has a related action')])
        result=validate_result(raw,self.row,self.pool)
        self.assertEqual(result['model_result'],'partial')
        self.assertEqual(result['result'],'unlocated')
        self.assertIn('disconnected',result['gate_failure'])

    def test_empty_rationale_is_not_a_semantic_decision(self):
        raw=dict(checks=[dict(id='M02-B01',result='supported',snippets=['S1'],edges=[],entry='S1',rationale='')])
        self.assertEqual(validate_result(raw,self.row,self.pool)['result'],'unlocated')


if __name__=='__main__':unittest.main()
