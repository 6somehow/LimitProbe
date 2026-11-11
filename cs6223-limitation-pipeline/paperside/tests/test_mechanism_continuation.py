import json
import tempfile
import unittest
from pathlib import Path

from paperprobe.continuation_finalize import parse_saved
from paperprobe.continuation_targeted import apply_edit_patch
from paperprobe.independent_discovery import validate_local
from paperprobe.mechanism_continuation import draft_rows, related_pages


class ContinuationTest(unittest.TestCase):
    def test_related_pages_include_behavior_citations_without_passing_behaviors_to_source_step(self):
        mechanism=dict(pages=[8,9],evidence=[dict(page=8,quote='cover')])
        group=dict(behaviors=[dict(evidence=[dict(source='paper',locator='PDF p.7',quote='algorithm')])])
        self.assertEqual(related_pages(mechanism,group),[7,8,9])

    def test_syntax_repair_preserves_semantic_text_and_original_bytes(self):
        content='{"obligations":[{"id":"O12,"behavior":"Keep exactly this claim"}]}'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.json'
            path.write_text(json.dumps(dict(choices=[dict(finish_reason='stop',message=dict(content=content))])))
            original=path.read_bytes()
            value,repairs=parse_saved(path)
            self.assertEqual(value['obligations'][0]['behavior'],'Keep exactly this claim')
            self.assertEqual(value['obligations'][0]['id'],'O12')
            self.assertFalse(repairs[0]['semantic_text_changes'])
            self.assertEqual(path.read_bytes(),original)

    def test_other_json_damage_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.json'
            path.write_text(json.dumps(dict(choices=[dict(finish_reason='stop',message=dict(content='{"statement":"truncated'))])))
            with self.assertRaises(ValueError):parse_saved(path)

    def test_missing_empty_replacement_list_is_logged(self):
        raw=dict(obligation_checks=[dict(id='O1',status='covered',behavior_ids=['B1'])],
                 behavior_reviews=[dict(id='B1',issues=[],reason='atomic')],additions=[])
        result=validate_local(raw,[dict(id='O1')],[dict(id='B1')],['paper'],[1])
        self.assertEqual(result['behavior_reviews'][0]['replacements'],[])
        self.assertEqual(len(result['schema_normalizations']),1)
        self.assertNotIn('replacements',raw['behavior_reviews'][0])

    def test_conflicting_addition_is_visible_but_not_applied(self):
        originals=[dict(id='M02-B01',behavior='Original')]
        review=dict(behavior_reviews=[dict(id='M02-B01',issues=[],replacements=[])],
                    additions=[dict(behavior='Potential duplicate',obligation_ids=['O1'])],
                    consistency_flags=[dict(addition_index=1)])
        result=draft_rows('M02',originals,review)
        self.assertEqual(len(result['behaviors']),1)
        self.assertEqual(len(result['held_additions']),1)
        self.assertEqual(originals,[dict(id='M02-B01',behavior='Original')])

    def test_replacement_can_absorb_addition_without_duplicating_it(self):
        review=dict(behavior_reviews=[dict(id='M02-B01',issues=['compound'],reason='Two actions',replacements=[])],
            additions=[dict(behavior='Pop',obligation_ids=['O2'])],consistency_flags=[])
        def r(text):return dict(behavior=text,precondition='S exists',basis='explicit',kind='mechanism',
                               search_terms=['S'],evidence=[dict(page=1,quote='while S')])
        patch=dict(edits=[dict(id='M02-B01',reason='Separate',replacements=[r('Loop'),r('Pop')],absorbed_addition_indices=[1])])
        result=apply_edit_patch(review,patch,['while S'],[1])
        draft=draft_rows('M02',[dict(id='M02-B01',behavior='Loop and pop')],result)
        self.assertEqual(len(draft['behaviors']),2)
        self.assertEqual(len(draft['absorbed_additions']),1)
        self.assertEqual(review['behavior_reviews'][0]['replacements'],[])

    def test_split_keeps_origin_and_does_not_delete_flagged_duplicate(self):
        originals=[dict(id='M02-B01',behavior='Loop and pop'),dict(id='M02-B02',behavior='Pop')]
        review=dict(behavior_reviews=[dict(id='M02-B01',issues=['compound'],reason='two operations',
                                         replacements=[dict(behavior='Loop'),dict(behavior='Pop')]),
                                     dict(id='M02-B02',issues=['duplicate'],replacements=[])], additions=[])
        result=draft_rows('M02',originals,review)
        self.assertEqual([b['id'] for b in result['behaviors']],['M02-B01-R01','M02-B01-R02','M02-B02'])
        self.assertEqual(result['behaviors'][0]['origin_id'],'M02-B01')


if __name__=='__main__':unittest.main()
