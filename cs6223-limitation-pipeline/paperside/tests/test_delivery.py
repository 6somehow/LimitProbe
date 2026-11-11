import sys,unittest,os,tempfile
from unittest.mock import patch
from pathlib import Path
from paperprobe.delivery import span_evidence,exact_evidence,find_team_repo,TEAM
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from finalize_handoff import numeric_scope
from schema.models import ScopeItem,Binding,Condition
from codeside.scope_check import ScopeChecker

class DeliveryTests(unittest.TestCase):
 def test_shared_consumer_locator_accepts_explicit_repository(self):
  with patch.dict(os.environ, {'PAPERPROBE_TEAM_REPO': str(TEAM)}):
   self.assertEqual(find_team_repo(),TEAM)
 def test_explicit_wrong_consumer_path_fails_instead_of_silent_fallback(self):
  with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'PAPERPROBE_TEAM_REPO': folder}):
   with self.assertRaisesRegex(FileNotFoundError,'PAPERPROBE_TEAM_REPO'):find_team_repo()

 def test_selected_span_preserves_pdf_bytes_instead_of_model_typography(self):
  pages=['Header\nTensor quantiza-\ntion uses ﬁelds.\nFooter']
  ev=span_evidence([dict(page=1,start_line=2,end_line=3)],pages)[0]
  self.assertEqual(ev['quote'],'Tensor quantiza-\ntion uses ﬁelds.')
  self.assertIn(ev['quote'],pages[0])
 def test_selected_spans_cannot_claim_unseen_pages_or_lines(self):
  for span in [dict(page=2,start_line=1,end_line=1),dict(page=1,start_line=0,end_line=1),dict(page=1,start_line=1,end_line=3),dict(page=1,start_line=2,end_line=1)]:
   with self.subTest(span=span),self.assertRaises(ValueError):span_evidence([span],['one\ntwo'])
 def test_source_span_cannot_quote_an_unbounded_page_as_evidence(self):
  with self.assertRaises(ValueError):span_evidence([dict(page=1,start_line=1,end_line=27)],['x\n'*28])
 def test_approximate_model_quote_does_not_become_verbatim_evidence(self):
  self.assertEqual(exact_evidence([dict(page=1,quote='quantization')],['quantiza-\ntion']),[])
 def test_nonnumeric_scope_must_not_enter_actual_consumer_unconstrained(self):
  s=ScopeItem(scope_id='s',artifact_id='a',param='width',kind='free_text',explicit=True,evidence=[])
  b=Binding(binding_id='b',artifact_id='a',paper_term='width',kind='parameter',code_symbol='x')
  c=Condition(expr='x < -100',params=['x'])
  # This is the consumer behavior the adapter must guard, not a desired scope judgment.
  self.assertEqual(ScopeChecker([s],[],[b]).check(c).scope_status,'in_scope')
  active=[b] if numeric_scope(s.model_dump()) else []
  self.assertEqual(ScopeChecker([s],[],active).check(c).scope_status,'unknown')
 def test_literal_numeric_domain_reaches_consumer_without_widening(self):
  s=ScopeItem(scope_id='s',artifact_id='a',param='block_size',kind='set',values=[64,128],explicit=True,evidence=[])
  b=Binding(binding_id='b',artifact_id='a',paper_term='block_size',kind='parameter',code_symbol='bs')
  self.assertTrue(numeric_scope(s.model_dump()))
  self.assertEqual(ScopeChecker([s],[],[b]).check(Condition(expr='bs == 96',params=['bs'])).scope_status,'out_of_scope')
 def test_strings_booleans_and_empty_ranges_are_not_numeric_domains(self):
  for s in [dict(kind='set',values=['A100']),dict(kind='set',values=[True]),dict(kind='interval',lower=None,upper=None),dict(kind='boolean',values=[True,False])]:
   self.assertFalse(numeric_scope(s))
 def test_navigation_bindings_do_not_claim_parameter_scope(self):
  s=ScopeItem(scope_id='s',artifact_id='a',param='width',kind='interval',lower=1,upper=4,evidence=[])
  b=Binding(binding_id='b',artifact_id='a',paper_term='width',kind='mechanism_entry',code_symbol='x',certain=False)
  self.assertEqual(ScopeChecker([s],[],[b]).check(Condition(expr='x > 8',params=['x'])).scope_status,'unknown')
