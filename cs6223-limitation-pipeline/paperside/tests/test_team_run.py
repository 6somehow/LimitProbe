import unittest

from paperprobe.team_run import draft, verify_checks


class TeamRunTest(unittest.TestCase):
    def test_unsupported_quote_rejected_without_losing_other_rows(self):
        valid = {"mechanism":"test","statement":"statement","kind":"other",
                 "evidence":[{"page":1,"quote":"A supported quote."}]}
        bad = {**valid, "evidence":[{"page":1,"quote":"An invented quote."}]}
        result, rejects = draft({"id":"p"},["A supported quote."],{
            "claims":[valid,bad],"scope":[],"eval_points":[],"limitations":[]})
        self.assertEqual(len(result["claims"]),1)
        self.assertEqual(len(rejects),1)

    def test_cross_target_citation_cannot_confirm_limitation(self):
        targets=[{"id":"l","kind":"limitation"}]
        code={"file":"one.py","line_start":1,"line_end":1,"snippet":"return x"}
        result, exported = verify_checks({"checks":[{"id":"l","result":"found",
            "excerpt_ids":["different"],"rationale":"reason"}]},targets,{"l":{"here":code}},"model")
        self.assertEqual(result[0]["result"],"unresolved")
        self.assertEqual(exported,[])

    def test_valid_partial_mapping_uses_team_verification_schema(self):
        targets=[{"id":"l","kind":"limitation"}]
        code={"file":"one.py","line_start":1,"line_end":1,"snippet":"return x"}
        _, exported = verify_checks({"checks":[{"id":"l","result":"weaker",
            "excerpt_ids":["here"],"rationale":"mechanism only"}]},targets,{"l":{"here":code}},"model")
        self.assertEqual(exported[0]["direction"],"paper_to_code")
        self.assertEqual(exported[0]["matching_code"],[code])
