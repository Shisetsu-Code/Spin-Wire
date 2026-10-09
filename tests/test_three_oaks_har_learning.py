import json
import tempfile
import threading
import unittest
from copy import deepcopy
from pathlib import Path
from tester_spin.providers.three_oaks.runtime import play_fields, continuation_fields, observed_spin_profile

FIXTURE = Path(__file__).parent / 'fixtures' / 'three_oaks_observed_rounds.json'
FAMILIES = {'3_coins': 'goreel', '3_aztec_temples': 'goreel', '3_china_pots': 'goreel',
            '3_egypt_chests': 'goreel', '3_african_drums': 'hraymo',
            '3_hot_teapots': 'hraymo', '3_superpower_diamonds': 'enjoy'}


class HARLearningTests(unittest.TestCase):
    def test_all_observed_payloads_match_saved_contracts(self):
        captures = json.loads(FIXTURE.read_text())
        count = 0
        for slug, records in captures.items():
            for record in records:
                action = record['request']['action']
                before = record['before'] if record['before'].get('context') else record['response']
                if action['name'] in ('spin', 'buy_spin'):
                    fields = play_fields(before, action['name'], action['params'].get('selected_mode'),
                                         game_slug=slug, family=FAMILIES[slug], client_profile=observed_spin_profile(slug,FAMILIES[slug]))
                else:
                    fields = continuation_fields(before, game_slug=slug, family=FAMILIES[slug], client_profile=observed_spin_profile(slug,FAMILIES[slug]))
                self.assertIsNotNone(fields, (slug, action))
                self.assertEqual(fields['action'], action)
                count += 1
        self.assertEqual(count, 55)

    def test_ambiguous_or_unknown_transitions_remain_pending(self):
        for actions, current in [(['pick'], 'bonus'), (['respin', 'pick'], 'bonus'),
                                 (['bonus_init'], 'bonus'), (['respin'], 'spins')]:
            data = {'context': {'round_finished': False, 'current': current, 'actions': actions}}
            self.assertIsNone(continuation_fields(data, game_slug='3_superpower_diamonds', family='enjoy'))
        self.assertIsNone(continuation_fields({'context': {'round_finished': False,
            'current': 'bonus', 'actions': ['respin']}}, game_slug='unknown', family='enjoy'))

    def test_both_purchases_finish_and_require_two_base_rounds(self):
        result, audits = self.run_adapter()
        self.assertEqual(result.status, 'OK', result.error)
        purchases = [a for a in result.attempts if a.mode_kind == 'PURCHASE']
        self.assertEqual(len(purchases), 2)
        self.assertTrue(all(a.terminal and a.wire_steps > 3 for a in purchases))
        self.assertTrue(all(a['status'] == 'CONFIRMED' and a['consecutive_base'] == 2 for a in audits))

    def test_endless_bonus_cannot_be_ok(self):
        result, _ = self.run_adapter(endless=True)
        self.assertEqual(result.status, 'PARCIAL')
        self.assertFalse(result.attempts[-1].terminal)
        self.assertLessEqual(result.attempts[-1].wire_steps, 81)

    def run_adapter(self, endless=False):
        from tester_spin.models import Game
        from tester_spin.providers.three_oaks.adapter import ThreeOaksProvider
        records = json.loads(FIXTURE.read_text())['3_superpower_diamonds']
        base = records[0]['before']
        chains = {}
        active = None
        for r in records:
            action = r['request']['action']
            if action['name'] == 'buy_spin':
                active = action['params']['selected_mode']
                chains[active] = []
            elif action['name'] == 'spin':
                active = None
            if active is not None:
                chains[active].append(r)
        config = {'options': {'token': 'fixture', 'queue': 'fixture', 'protocol': 'goreel', 'wl': 'demo'},
                  'desktop': {'server_url': '//betman-demo.head.3oaks.com/betman-demo/gs/3_superpower_diamonds/desktop/{QUEUE}/demo/',
                              'client_url': 'https://static.3oaks.com/gs/clients_enjoy/demo/v1/'}}
        class Response:
            def __init__(self, data=None, text=None):
                self.data = data
                self.text = text if text is not None else json.dumps(data)
            def raise_for_status(self): pass
            def json(self): return self.data
        config['gr']={'static_path':'https://static.3oaks.com/gs/gamerunner/v1/'}
        def adapter_source(url):
            if url.endswith('init.js'): return 'window._PROVIDER.game={name:"synthetic",use:["protocol","ui"]};'
            if url.endswith('gr.js'): return (FIXTURE.parent/'three_oaks_shared_runner.js').read_text()
            return (FIXTURE.parent/'three_oaks_legacy_flow.js').read_text()+';function actBuyFeature(optionType){var params={};params.bet_per_line=GR.UI.model.get("bet_per_line");params.lines=app.model.gameLines();params.selected_mode=optionType;app.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN,params)}'
        class HTTP:
            queue = []
            def get(self, url, **kwargs):
                return Response(text='})(window, ' + json.dumps(config) + ', "url");') if url.endswith('/play') else Response(text=adapter_source(url))
            def post(self, url, **kwargs):
                body = json.loads(kwargs['data'])
                if body['command'] != 'play':
                    return Response({**deepcopy(base), 'session_id': 'fixture'})
                action = body['action']
                if action['name'] == 'buy_spin':
                    self.queue = list(chains[action['params']['selected_mode']])
                if self.queue:
                    observed = self.queue.pop(0)
                    assert action == observed['request']['action']
                    data = deepcopy(observed['response'])
                    if endless and action['name'] == 'respin':
                        self.queue.insert(0, observed)
                else:
                    assert action == {'name': 'spin', 'params': {'bet_per_line': 10, 'lines': 25}}
                    data = deepcopy(base)
                return Response(data)
        with tempfile.TemporaryDirectory() as directory:
            provider = ThreeOaksProvider(Path(directory))
            provider.http = HTTP()
            result = provider.test_game(Game('3oaks', '3_superpower_diamonds', '3 SuperPower Diamonds',
                'https://3oaks.com/game/3_superpower_diamonds'), spins=2, timeout_s=1,
                stop_event=threading.Event(), progress=lambda _: None)
            audits = [json.loads(p.read_text()) for p in Path(result.run_dir).glob('attempt-*/return-to-base.json')]
            return result, audits


if __name__ == '__main__':
    unittest.main()
