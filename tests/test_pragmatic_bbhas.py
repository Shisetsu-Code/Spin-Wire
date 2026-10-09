import importlib.util
import json
from pathlib import Path
from urllib.parse import parse_qsl
import unittest

from tester_spin.providers import pragmatic_observed_transitions as module
root = Path(__file__).parent / 'fixtures'

class HoldSpinnerHAR(unittest.TestCase):
    def test_every_observed_active_bonus_uses_zero_selector(self):
        steps = json.loads((root / 'pragmatic_bbhas_har.json').read_text(encoding='utf-8-sig'))
        for step in steps:
            response = dict(parse_qsl(step['response']))
            if response.get('na') != 'b':
                continue
            with self.subTest(index=response['index']):
                selection = module.observed_bonus_rule(response, 'vswaysbbhas')
                self.assertIsNotNone(selection)
                self.assertEqual(selection['fields'], {'ind': '0'})
                self.assertEqual(selection['domain'], ['0'])
                self.assertIsNone(module.observed_bonus_rule(response, 'unrelated'))
                with self.assertRaises(ValueError):
                    module.observed_bonus_rule(response, 'vswaysbbhas', override='1')

    def test_unknown_or_finished_state_is_not_authorized(self):
        for group in ['{bg:{bgid:"0",bgt:"69",end:"1",level:"3",lifes:"0",rw:"88.00"}}',
                      '{bg:{bgid:"0",bgt:"69",end:"0",level:"99",lifes:"3",rw:"0.00"}}',
                      '{bg:{bgid:"0",bgt:"69",end:"0",level:"0",lifes:"3",rw:"0.00",ask:"1"}}']:
            self.assertIsNone(module.observed_bonus_rule({'na':'b','g':group}, 'vswaysbbhas'))

if __name__ == '__main__':
    unittest.main()
