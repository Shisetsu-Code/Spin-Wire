"""Resolve active 3 Oaks input values, not only the names of wire fields."""
import copy
from pathlib import Path
import unittest

from tester_spin.providers.three_oaks.source_inputs import source_purchase_contract
from tester_spin.providers.three_oaks.runtime import play_fields

FIXTURE = Path(__file__).parent / 'fixtures' / 'three_oaks_modern_purchase.js'


def state(modes=None):
    return {'context': {'current': 'spins', 'round_finished': True,
                        'actions': ['spin', 'buy_spin'],
                        'spins': {'bet_per_line': 1, 'lines': 20},
                        'available_buy_bonus': [1] if modes is None else modes},
            'settings': {'lines': [40], 'bet_factor': [1], 'version': '2'}}


def numeric_source():
    source = FIXTURE.read_text().replace(
        'lines:Y.bus.getUI("lines")}},t)',
        'lines:Y.bus.getUI("lines"),selected_mode:r}},t)')
    source = source.replace(';Y.bus.sendPlayAsync({name:"buy_spin"',
        ';var r=Y.serverData.get("version")?Number(t):String(t);Y.bus.sendPlayAsync({name:"buy_spin"')
    return source + ';t.set("version",(function(t){var e;return null!==(e=t.settings.version)&&void 0!==e?e:null}));'


class WireValueTests(unittest.TestCase):
    def test_spin_reads_settings_lines_first_as_in_unmodified_client_fixture(self):
        data = state()
        profile = source_purchase_contract(FIXTURE.read_text(), data)
        self.assertEqual(play_fields(data, 'spin', client_profile=profile)['action']['params'],
                         {'bet_per_line': 1, 'lines': 40})

    def test_purchase_keeps_its_own_ui_lines_source(self):
        data = state()
        profile = source_purchase_contract(FIXTURE.read_text(), data)
        self.assertEqual(play_fields(data, 'buy_spin', 1, client_profile=profile)['action']['params'],
                         {'bet_per_line': 1, 'lines': 20})

    def test_purchase_can_read_settings_lines_without_overwriting_spin_source(self):
        source = FIXTURE.read_text().replace('lines:Y.bus.getUI("lines")}},t)',
                                             'lines:Y.serverData.get("settingsLines")[0]}},t)')
        data = state()
        profile = source_purchase_contract(source, data)
        self.assertEqual(play_fields(data, 'buy_spin', 1, client_profile=profile)['action']['params']['lines'], 40)

    def test_missing_declared_settings_source_is_not_replaced_with_context(self):
        data = state()
        data['settings']['lines'] = []
        profile = source_purchase_contract(FIXTURE.read_text(), data)
        with self.assertRaises(ValueError):
            play_fields(data, 'spin', client_profile=profile)

    def test_dynamic_unresolved_settings_index_is_not_guessed(self):
        source = FIXTURE.read_text().replace('settingsLines")[0]',
                                             'settingsLines")[Y.bus.setUI("lines",t.value)]')
        data = state()
        profile = source_purchase_contract(source, data)
        with self.assertRaises(ValueError):
            play_fields(data, 'spin', client_profile=profile)

    def test_conflicting_spin_sources_do_not_certify_one_arbitrary_route(self):
        source = FIXTURE.read_text() + ';Y.bus.sendPlayAsync({name:"spin",params:{bet_per_line:Y.bus.getUI("bet_per_line"),lines:Y.bus.getUI("lines")}},null)'
        profile = source_purchase_contract(source, state())
        self.assertFalse(profile.get('spin_params'))

    def test_declared_number_conversion_is_applied_to_announced_text_selector(self):
        data = state(['1'])
        profile = source_purchase_contract(numeric_source(), data)
        self.assertEqual(profile['purchase_selector_type'], 'number')
        value = play_fields(data, 'buy_spin', '1', client_profile=profile)['action']['params']['selected_mode']
        self.assertIs(type(value), int)
        self.assertEqual(value, 1)

    def test_non_numeric_or_non_finite_selector_is_rejected(self):
        for selector in ['invalid', 'NaN', 'Infinity', '-Infinity']:
            with self.subTest(selector=selector):
                data = state([selector])
                profile = source_purchase_contract(numeric_source(), data)
                with self.assertRaises(ValueError):
                    play_fields(data, 'buy_spin', selector, client_profile=profile)

    def test_numeric_selector_does_not_mutate_source_context(self):
        data = state(['1'])
        before = copy.deepcopy(data)
        play_fields(data, 'buy_spin', '1', client_profile=source_purchase_contract(numeric_source(), data))
        self.assertEqual(data, before)


if __name__ == '__main__':
    unittest.main()
