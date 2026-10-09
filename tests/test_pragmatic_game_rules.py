import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tester_spin.providers.pragmatic import PragmaticProvider
from tester_spin.providers.pragmatic_observed_transitions import (
    apply_spin_rule, observed_continuation, observed_next_action,
)


class GameRules(unittest.TestCase):
    def test_888_gold_uses_observed_five_line_wire_and_terminal(self):
        fields = {'action':'doSpin','l':'10','bl':'0','sInfo':'n'}
        apply_spin_rule(fields,'cs5triple8gold')
        self.assertEqual(fields,{'action':'doSpin','l':'5'})
        self.assertEqual(observed_next_action({'gs':'0','w':'0.08'},'cs5triple8gold'),'s')
        self.assertEqual(observed_next_action({'gs':'0','fs':'1'},'cs5triple8gold'),'')
    def test_extra_juicy_selector_is_scoped_to_observed_states(self):
        from tester_spin.providers.pragmatic_observed_transitions import observed_bonus_rule
        state={'na':'b','bgt':'35','bgid':'0','end':'0','level':'0','status':'0,1,0,0,0'}
        self.assertEqual(observed_bonus_rule(state,'vswaysxjuicy')['fields'],{'ind':'1'})
        self.assertIsNone(observed_bonus_rule(state,'unknown'))
        self.assertIsNone(observed_bonus_rule({**state,'level':'2'},'vswaysxjuicy'))
        with self.assertRaises(ValueError):observed_bonus_rule(state,'vswaysxjuicy',override=0)
    def test_profile_does_not_hide_server_error(self):
        from tester_spin.providers.pragmatic_har_protocol import analyze_response
        self.assertEqual(analyze_response({'na': 'buy', 'error': 'denied'}, symbol='scdiamond')['state_kind'], 'server_error')

    def test_free_card_resets_consecutive_base_cycles(self):
        from tester_spin.provider_return_checks import pragmatic_check
        ordinary = [{'na': 'play', 't_left': '1'}, {'na': 'end', 't_left': '0', 'fs_left': '0'}, {'na': 'collect'}, {'na': 'buy'}]
        responses = [{'na': 'play', 't_left': '1', 'fs_left': '1'}, {'na': 'end', 't_left': '1', 'fs_left': '1'}] + ordinary * 3
        with tempfile.TemporaryDirectory() as tmp:
            provider = PragmaticProvider(Path(tmp))
            provider._post_and_store = lambda *a, **kw: (200, b'', responses.pop(0), {})
            proof = pragmatic_check(provider, SimpleNamespace(symbol='scdiamond', reel_contract=None), {'na': 'buy'}, {'symbol': 'scdiamond'}, Path(tmp), 1)
        self.assertEqual(proof['status'], 'CONFIRMED')
        self.assertEqual([row['base'] for row in proof['probes']], [False, True, True])

    def test_classification_uses_the_same_profile_as_execution(self):
        from tester_spin.providers.pragmatic_har_protocol import analyze_response
        for state, action in [('play', 'doPlay'), ('end', 'doEnd'), ('collect', 'doCollect')]:
            result = analyze_response({'na': state}, symbol='scdiamond')
            self.assertEqual(result['automatic_handler'], action)
            self.assertFalse(result['terminal_hint'])
        self.assertTrue(analyze_response({'na': 'buy'}, symbol='scdiamond')['terminal_hint'])
        self.assertFalse(analyze_response({'na': 'buy'}, symbol='unknown')['terminal_hint'])

    def test_scratchcard_closes_and_collects_before_next_purchase(self):
        from tester_spin.provider_return_checks import pragmatic_check
        responses = [
            {'na': 'play', 't_left': '1'},
            {'na': 'end', 't_left': '0', 'fs_left': '0'},
            {'na': 'collect'},
            {'na': 'buy'},
        ] * 2
        actions = []
        with tempfile.TemporaryDirectory() as tmp:
            provider = PragmaticProvider(Path(tmp))
            def send(bootstrap, fields, *args, **kwargs):
                apply_spin_rule(fields, bootstrap.symbol)
                actions.append(fields['action'])
                self.assertFalse({'c', 'l', 'bl', 'sInfo'} & fields.keys())
                self.assertEqual('tickets' in fields, fields['action'] == 'doBuy')
                return 200, b'', responses.pop(0), {}
            provider._post_and_store = send
            proof = pragmatic_check(provider, SimpleNamespace(symbol='scdiamond', reel_contract=None),
                {'na': 'buy'}, {'symbol': 'scdiamond', 'c': '1', 'l': '10', 'sInfo': 'n'}, Path(tmp), 1)
        self.assertEqual(proof['status'], 'CONFIRMED')
        self.assertEqual(actions, ['doBuy', 'doPlay', 'doEnd', 'doCollect'] * 2)

    def test_scratchcard_end_is_a_continuation(self):
        state = {'na': 'end', 't_left': '0', 'fs_left': '0'}
        self.assertEqual(observed_next_action(state, 'scdiamond'), 'end')
        self.assertEqual(observed_continuation(state, 'scdiamond'), 'doEnd')
        self.assertEqual(observed_next_action({'na': 'buy', 'fs_left': '1'}, 'scdiamond'), 'buy')

    def test_legacy_wire_fields_and_terminal_are_scoped(self):
        fields = {'action': 'doSpin', 'l': '10', 'bl': '0', 'sInfo': 'n'}
        apply_spin_rule(fields, 'cs3w')
        self.assertEqual(fields, {'action': 'doSpin', 'l': '3'})
        self.assertEqual(observed_next_action({'gs': '0'}, 'cs3w'), 's')
        self.assertEqual(observed_next_action({'gs': '0'}, 'unknown'), '')

    def test_zeus_and_unknown_games_do_not_share_overrides(self):
        fields = {'action': 'doSpin', 'l': '10'}
        apply_spin_rule(fields, 'vs15godsofwar')
        self.assertEqual(fields['l'], '15')
        self.assertEqual(fields['ind'], '1')
        unknown = {'action': 'doSpin', 'l': '10'}
        apply_spin_rule(unknown, 'unknown')
        self.assertEqual(unknown, {'action': 'doSpin', 'l': '10'})
