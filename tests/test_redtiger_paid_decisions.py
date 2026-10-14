import unittest,json,copy
from pathlib import Path
from tester_spin.providers.redtiger import base_state
class PaidDecisionTests(unittest.TestCase):
 def fixtures(self):return json.loads((Path(__file__).parent/'fixtures/redtiger_paid_decision_rounds.json').read_text(encoding='utf-8'))
 def test_captured_choice_rounds_close_without_second_wager(self):
  for group in self.fixtures()['choice_rounds']:
   if not group['steps']:continue
   self.assertTrue(base_state.settled_paid_choice_round(group['entry']['request'],group['entry']['response'],[(s['request'],s['response']) for s in group['steps']]))
 def test_monetary_or_round_mismatch_cannot_confirm_choice_round(self):
  group=self.fixtures()['choice_rounds'][0]
  for kind in ['round','debit','pending']:
   steps=copy.deepcopy(group['steps'])
   if kind=='round':steps[-1]['response']['result']['transactions']['roundId']+=1
   elif kind=='debit':steps[-1]['response']['result']['user']['balance']['cash']['afterBet']='0'
   else:steps[-1]['response']['result']['game']['choices']={'selected':None,'available':['continue','collect']}
   self.assertFalse(base_state.settled_paid_choice_round(group['entry']['request'],group['entry']['response'],[(s['request'],s['response']) for s in steps]))
 def test_other_captured_normal_paid_rounds(self):
  for row in self.fixtures()['captures'][:2]:
   for previous,current in zip(row['rounds'],row['rounds'][1:]):
    self.assertTrue(base_state.classify_base_state(current['response'],request=current['request'],previous=previous['response'])['base'])

 def test_return_probe_finishes_choices_instead_of_demanding_empty_spin(self):
  import tempfile,threading
  from unittest.mock import patch
  from types import SimpleNamespace
  from tester_spin.provider_return_checks import redtiger_check
  groups=[g for g in self.fixtures()['choice_rounds'] if len(g['steps'])==1 and g['steps'][0]['request']['choice']=='collect'][:2]
  spins=[(200,g['entry']['request'],g['entry']['response'],[]) for g in groups]
  replies=[(200,'https://g/choice',g['steps'][0]['request'],g['steps'][0]['response'],[]) for g in groups]
  import copy
  from decimal import Decimal
  first=copy.deepcopy(groups[0]);second=copy.deepcopy(groups[0]);new_id=first['entry']['response']['result']['transactions']['roundId']+1
  second['entry']['response']['result']['transactions']['roundId']=new_id
  second['steps'][0]['request']['roundId']=new_id;second['steps'][0]['response']['result']['transactions']['roundId']=new_id
  cash=first['steps'][0]['response']['result']['user']['balance']['cash'];start=cash['atEnd'];after=str(Decimal(start)-Decimal('0.1'));end=str(Decimal(after)+Decimal('0.11'))
  second['entry']['response']['result']['user']['balance']['cash']={'atStart':start,'afterBet':after,'atEnd':after}
  second['steps'][0]['response']['result']['user']['balance']['cash']={'atStart':after,'afterBet':after,'atEnd':end}
  spins=[(200,g['entry']['request'],g['entry']['response'],[]) for g in [first,second]]
  replies=[(200,'https://g/choice',g['steps'][0]['request'],g['steps'][0]['response'],[]) for g in [first,second]]
  with tempfile.TemporaryDirectory() as tmp,patch('tester_spin.providers.redtiger.execution._post_spin',side_effect=spins),patch('tester_spin.providers.redtiger.execution._post_choice',side_effect=replies):
   proof=redtiger_check(SimpleNamespace(default_stake=0.1),Path(tmp),1,threading.Event())
   self.assertEqual(proof['status'],'CONFIRMED',proof)
   self.assertEqual([len(p['captures']) for p in proof['probes']],[2,2])

 def test_repeating_ladder_covers_actions_without_infinite_prefixes(self):
  import tempfile
  from tester_spin.models import GameTestResult,SpinAttempt
  from tester_spin.providers.redtiger.runtime import choice_transition,pending_choice_from_response
  from tester_spin.providers.redtiger.branch_coverage import _seed_from_base_attempt
  group=self.fixtures()['choice_rounds'][0];before=group['entry']['response'];records=[]
  for step in group['steps']:
   prompt=pending_choice_from_response(before);records.append(choice_transition(prompt,step['request']['choice'],step['response']));before=step['response']
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);attempt=root/'SPIN'/'attempt-00001';attempt.mkdir(parents=True)
   (attempt/'summary.json').write_text(json.dumps({'choice_continuations':records}),encoding='utf-8')
   result=GameTestResult(provider='redtiger',slug='x',game_name='x',game_url='',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',attempts=[SpinAttempt(number=1,ok=True,terminal=True,artifact_dir=str(attempt))])
   points={};queue=_seed_from_base_attempt(result,run_root=root,base_mode='SPIN',repetition=1,branch_points=points)
   self.assertEqual(len(points),1)
   self.assertEqual(next(iter(points.values())).covered,{'continue','collect'})
   self.assertEqual(queue,[])
   marker=next(m for m in result.discovered_modes if m.get('source')=='choice_transition.gameData.progress.level')
   self.assertEqual(marker['kind'],'DIAGNOSTIC')
   self.assertIs(marker['coverage_required'],False)

 def test_active_feature_at_entry_or_middle_is_not_a_base_probe(self):
  group=self.fixtures()['choice_rounds'][0]
  for target in ['entry','middle']:
   value=copy.deepcopy(group)
   payload=value['entry']['response'] if target=='entry' else value['steps'][0]['response']
   payload['result']['game']['fsp']={'active':True}
   self.assertFalse(base_state.settled_paid_choice_round(value['entry']['request'],value['entry']['response'],[(s['request'],s['response']) for s in value['steps']]))

 def test_ladder_preserves_an_outer_choice_prefix(self):
  import tempfile
  from tester_spin.models import GameTestResult,SpinAttempt
  from tester_spin.providers.redtiger.runtime import choice_transition,pending_choice_from_response
  from tester_spin.providers.redtiger.branch_coverage import _seed_from_base_attempt
  group=self.fixtures()['choice_rounds'][0];before=group['entry']['response']
  records=[{'round_id':before['result']['transactions']['roundId'],'available':['left','right'],'selected':'left'}]
  for step in group['steps']:
   records.append(choice_transition(pending_choice_from_response(before),step['request']['choice'],step['response']));before=step['response']
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);attempt=root/'SPIN'/'attempt-00001';attempt.mkdir(parents=True)
   (attempt/'summary.json').write_text(json.dumps({'choice_continuations':records}),encoding='utf-8')
   result=GameTestResult(provider='redtiger',slug='x',game_name='x',game_url='',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',attempts=[SpinAttempt(number=1,ok=True,terminal=True,artifact_dir=str(attempt))])
   points={};queue=_seed_from_base_attempt(result,run_root=root,base_mode='SPIN',repetition=1,branch_points=points)
   self.assertEqual(set(points),{('SPIN',()),('SPIN',('left',))})
   self.assertEqual(points[('SPIN',())].required,['left','right'])
   self.assertEqual(points[('SPIN',('left',))].covered,{'continue','collect'})
   self.assertEqual(queue,[('right',)])

 def test_inline_respin_requires_explicit_last_frame(self):
  group=copy.deepcopy(self.fixtures()['choice_rounds'][7])
  frames=group['steps'][0]['response']['result']['game']['gameData']['respin']
  self.assertIs(frames[-1]['isLast'],True)
  frames[-1]['isLast']=False
  self.assertFalse(base_state.settled_paid_choice_round(group['entry']['request'],group['entry']['response'],[(s['request'],s['response']) for s in group['steps']]))

 def test_nested_non_normal_outcome_is_not_a_base_probe(self):
  for mode in [1,False]:
   group=copy.deepcopy(self.fixtures()['choice_rounds'][0])
   group['steps'][-1]['response']['result']['game']['nested']={'gameMode':mode,'hasState':True,'win':{'total':'0'},'features':[]}
   self.assertFalse(base_state.settled_paid_choice_round(group['entry']['request'],group['entry']['response'],[(s['request'],s['response']) for s in group['steps']]))

 def test_prior_repetition_cannot_replace_new_required_sample(self):
  import tempfile
  from tester_spin.models import GameTestResult,SpinAttempt
  from tester_spin.providers.redtiger.runtime import choice_transition,pending_choice_from_response
  from tester_spin.providers.redtiger.branch_coverage import _seed_from_base_attempt
  group=self.fixtures()['choice_rounds'][1];entry=group['entry']['response'];step=group['steps'][0]
  record=choice_transition(pending_choice_from_response(entry),step['request']['choice'],step['response'])
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);attempt=root/'SPIN'/'attempt-00001';attempt.mkdir(parents=True)
   (attempt/'summary.json').write_text(json.dumps({'choice_continuations':[record]}),encoding='utf-8')
   result=GameTestResult(provider='redtiger',slug='x',game_name='x',game_url='',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',attempts=[SpinAttempt(number=1,ok=True,terminal=True,artifact_dir=str(attempt))])
   points={};_seed_from_base_attempt(result,run_root=root,base_mode='SPIN',repetition=1,branch_points=points)
   points[('SPIN',())].covered.add('collect');points[('SPIN',())].sample_counts['collect']=1
   queue=_seed_from_base_attempt(result,run_root=root,base_mode='SPIN',repetition=1,branch_points=points)
   self.assertEqual(queue,[('collect',)])
