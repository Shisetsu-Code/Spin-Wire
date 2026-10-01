from __future__ import annotations
import json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import MagicMock
from tester_spin.models import Game
from tester_spin.providers.ka_gaming.adapter import KAGamingProvider

CLIENT='''Cc.I9e=function(a,b){var d=Nb.w4d(),e=Ob.vFc(a+"2070"+b.JKb+d),f=Ob.vFc(d+b.JKb+b.fKb),g=$b.Bb().PXh(),e=Rb(0==e%2?d+"1.0.266 (2070)"+e+g+f+a+"2070":g+a+f+b.fKb+e+"2070"+d);b.Jub=e+d}; PXh:function(){return"fixture-public-client-literal"}'''
class KARMPExecutionTests(unittest.TestCase):
 def run_demo(self, spin, allowed_cps=None, extra_modes=None, initial_state=None):
  directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
  root=Path(directory.name);provider=KAGamingProvider(root)
  cache=provider.provider_root/'runtime';cache.mkdir();(cache/'game.min.2070.js').write_text(CLIENT)
  if extra_modes:
   provider._catalog_modes["goldenbull"] = [{"id":"SPIN"}] + extra_modes
  requests=[]
  initial={'sgr':{'lsd':{'sel':5,'cps':1,'atb':0,'dn':0.01,'fs':False,'rf':0,'acb':0}},'un':'server-user','si':'fresh-session','e':False,'ec':0}
  if initial_state is not None: initial['sgr']['lsd']=initial_state
  if allowed_cps is not None: initial['cup']=allowed_cps
  def post(url,**kwargs):
   requests.append((url,json.loads(kwargs['data']),json.loads(kwargs['headers']['ctx'])))
   response=MagicMock(status_code=200,text=json.dumps(initial if len(requests)==1 else spin))
   response.json.return_value=initial if len(requests)==1 else spin
   return response
  provider.http=MagicMock();provider.http.post.side_effect=post
  provider.http.get.side_effect=[MagicMock(status_code=200,text='script.src="game.min.2070.js"'),MagicMock(status_code=200,text=CLIENT)]
  result=provider.test_game(Game('ka_gaming','goldenbull','GoldenBull','https://gamesdemo.kaga88.com/?g=GoldenBull&p=demo&u=123&t=123&ak=accessKey&cr=USD&loc=es',symbol='GoldenBull'),spins=1,timeout_s=2,stop_event=threading.Event(),progress=lambda _:None)
  return result,requests
 def test_cached_client_executes_fresh_authenticated_terminal_spin(self):
  result,requests=self.run_demo({'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0,'sel':5,'cps':1,'atb':0,'dn':0.01}})
  self.assertEqual(result.status,'OK')
  self.assertEqual(result.successful_spins,1)
  self.assertEqual(len(requests),3)
  self.assertEqual(requests[1][2]['u'],'server-user')
  self.assertEqual(requests[1][2]['c'],'fresh-session')
  self.assertEqual(requests[1][1]['sel'],5)
  self.assertEqual(requests[1][1]['dn'],0.01)
  self.assertTrue(result.attempts[0].terminal)
 def test_provider_rejection_never_counts_as_success(self):
  result,_=self.run_demo({'e':True,'ec':6,'es':'not authenticated'})
  self.assertEqual(result.status,'ERROR')
  self.assertEqual(result.successful_spins,0)
 def test_active_free_games_stay_partial(self):
  result,_=self.run_demo({'e':False,'ec':0,'md':{'fs':True,'rf':0,'acb':0}})
  self.assertEqual(result.status,'PARCIAL')
  self.assertEqual(result.successful_spins,0)
  self.assertEqual(len(result.attempts),1)
  self.assertFalse(result.attempts[0].terminal)

 def test_stale_state_bet_uses_advertised_allowed_coin_step(self):
  result,requests=self.run_demo({'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0}},allowed_cps=[5,10,15])
  self.assertEqual(requests[1][1]['cps'],5)


 def test_remote_session_is_closed_after_success_and_rejection(self):
  for spin in ({'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0}}, {'e':True,'ec':6}):
   _,requests=self.run_demo(spin)
   self.assertTrue(requests[-1][0].endswith('/rmp/endSession'))
   self.assertEqual(requests[-1][1],{'es':'quit'})
   self.assertEqual(requests[-1][2]['c'],'fresh-session')


 def test_completed_inline_additional_spins_do_not_require_another_request(self):
  state={'fs':False,'rf':0,'acb':0,'fsr':0,'mb':False,'sel':10,'cps':5,'atb':0,'dn':.01,
   'as':[{'asi':123,'st':[7,6,3,0,6,7,4,3,0,4,7,5,4,0,4],'swi':[0]*20,'snm':[0]*20,'ssm':[0]*20,
          'swm':0,'sw':0,'swu':0,'fsw':0,'sm':[0,3],'tw':50}]}
  result,requests=self.run_demo({'e':False,'ec':0,'md':state})
  self.assertEqual(result.status,'OK')
  self.assertEqual(result.successful_spins,1)
  self.assertEqual(len(requests),3)
  self.assertTrue(result.attempts[0].terminal)
 def test_unknown_or_incomplete_additional_spin_blocks_remain_partial(self):
  for additional in ([{'choice':1}],[{'asi':123,'st':[1,2,3],'tw':10}],{'pending':True}):
   result,_=self.run_demo({'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0,'fsr':0,'as':additional}})
   self.assertEqual(result.status,'PARCIAL')
   self.assertEqual(result.successful_spins,0)

 def test_informational_catalog_features_do_not_downgrade_terminal_base_spin(self):
  result,_=self.run_demo({'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0}},
   extra_modes=[{'id':'WILD_FEATURE','kind':'FEATURE','coverage_required':False},
                {'id':'FREE_GAMES','kind':'FEATURE','coverage_required':False}])
  self.assertEqual(result.status,'OK')
  self.assertEqual(result.successful_spins,1)

 def test_required_unvalidated_feature_still_downgrades_terminal_spin(self):
  result,_=self.run_demo({'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0}},
   extra_modes=[{'id':'UNKNOWN_REQUIRED','coverage_required':True}])
  self.assertEqual(result.status,'PARCIAL')

 def test_agent_angels_inline_screen_is_terminal_at_start_and_after_spin(self):
  state={'fs':False,'rf':0,'acb':0,'fsr':0,'mb':False,'sel':5,'cps':1,'atb':0,'dn':.01,
   'as':[{'asi':254815267,'st':[7,8,3,7,8,5,10,6,5,10,6,6,10,7,6,7,7,2],
          'swm':0,'sw':0,'swu':0,'fsw':0,'tw':0}]}
  result,requests=self.run_demo({'e':False,'ec':0,'md':state},initial_state=state)
  self.assertEqual(result.status,'OK')
  self.assertEqual(result.successful_spins,1)
  self.assertEqual(len(requests),3)

 def test_each_game_test_has_one_fresh_session_not_one_per_spin(self):
  spin={'e':False,'ec':0,'md':{'fs':False,'rf':0,'acb':0}}
  _,first=self.run_demo(spin)
  _,second=self.run_demo(spin)
  self.assertNotEqual(first[0][2]['idv'],second[0][2]['idv'])
  self.assertNotEqual(first[0][1]['un'],second[0][1]['un'])
  self.assertEqual(sum(u.endswith('/rmp/startGame') for u,b,c in first),1)
  self.assertEqual(first[1][2]['idv'],first[2][2]['idv'])
