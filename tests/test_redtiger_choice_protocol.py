import unittest
from tester_spin.providers.redtiger import runtime
class ChoiceProtocolTests(unittest.TestCase):
 def response(self,choices,round_id=3):
  return {'success':True,'result':{'transactions':{'roundId':round_id},'game':{'choices':choices,'win':{'total':'0'},'hasState':True}}}
 def test_dynamic_pending_state_and_resolved_state(self):
  p=self.response({'selected':None,'available':['continue','collect']})
  self.assertEqual(runtime.choice_state(p)['status'],'PENDING')
  p['result']['game']['gameData']={'selected':'continue'}
  self.assertEqual(runtime.choice_state(p)['status'],'PENDING')
  p['result']['game']['choices']={'selected':'collect','available':None}
  self.assertEqual(runtime.choice_state(p)['status'],'RESOLVED')
 def test_malformed_remote_choices_cannot_look_terminal(self):
  for value in [{'available':['collect']},{'selected':'collect'}, {}, {'selected':None,'available':'collect'}, {'selected':None,'available':[]},{'selected':'collect','available':['continue']}]:
   p=self.response(value)
   self.assertEqual(runtime.choice_state(p)['status'],'UNKNOWN')
   self.assertTrue(runtime.validate_spin_response(p)[1])
 def test_round_change_is_not_an_accepted_choice_reply(self):
  prompt=runtime.ChoicePrompt(round_id=3,available=('collect',))
  self.assertTrue(runtime.choice_reply_warnings(prompt,'collect',self.response({'selected':'collect','available':None},4)))
 def test_resolved_picker_records_indexes_without_becoming_remote_choice(self):
  p={'success':True,'result':{'game':{'hasState':False,'win':{'total':'0'},'picker':{'options':[{'name':'Multiplier','value':2},{'name':'Multiplier','value':5}], 'choices':[{'name':'Multiplier','option':1}]}}}}
  self.assertIsNone(runtime.pending_choice_from_response(p))
  summary=runtime.response_summary(p)
  self.assertEqual(summary['resolved_pickers'][0]['resolved'],[{'index':1,'name':'Multiplier','value':5}])

 def test_captured_continue_can_keep_selector_pending_multiple_times(self):
  import json
  from pathlib import Path
  rows=json.loads((Path(__file__).parent/'fixtures/redtiger_astronaut_choices.json').read_text(encoding='utf-8'))
  chain=rows[2:6]
  self.assertEqual([runtime.choice_state(r['response'])['status'] for r in chain],['PENDING','PENDING','PENDING','RESOLVED'])
  for previous,current in zip(chain,chain[1:]):
   prompt=runtime.pending_choice_from_response(previous['response'])
   self.assertIn(current['request']['choice'],prompt.available)
   self.assertEqual(runtime.choice_reply_warnings(prompt,current['request']['choice'],current['response']),[])
   transition=runtime.choice_transition(prompt,current['request']['choice'],current['response'])
   self.assertEqual(transition['response_choice']['status'],runtime.choice_state(current['response'])['status'])
