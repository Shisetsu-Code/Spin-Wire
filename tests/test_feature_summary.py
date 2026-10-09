import unittest

from tester_spin.feature_summary import feature_summary, provider_summary_lines


class FeatureSummaryTests(unittest.TestCase):
    def test_failed_bootstrap_placeholder_does_not_prove_no_features(self):
        row = {'provider': 'belatra', 'status': 'ERROR', 'discovered_modes': [
            {'id': 'SPIN', 'kind': 'SPIN', 'automated': True, 'spin_validated': False}]}
        self.assertEqual(feature_summary(row),
            'Compras: Sin datos | Cantidad: Sin datos | Antebets: Sin datos')

    def test_unresolved_provider_buy_is_not_reported_as_absent(self):
        for provider, mid in [('yggdrasil', 'BUY_BONUS_UNRESOLVED'),
                              ('3oaks', 'AVAILABLE_BUY_FREESPINS')]:
            with self.subTest(provider=provider):
                row = {'provider': provider, 'discovered_modes': [
                    {'id': 'SPIN', 'kind': 'SPIN'},
                    {'id': mid, 'kind': 'UNKNOWN_FEATURE', 'executable': False,
                     'required_options': [0, 1]}]}
                self.assertEqual(feature_summary(row),
                    'Compras: Sin datos | Cantidad: Sin datos | Antebets: No')

    def test_unresolved_booster_is_not_reported_as_no_antebet(self):
        row = {'provider': '3oaks', 'discovered_modes': [
            {'id': 'SPIN', 'kind': 'SPIN'},
            {'id': 'AVAILABLE_BOOSTERS', 'kind': 'UNKNOWN_FEATURE',
             'executable': False, 'required_options': [0]}]}
        self.assertEqual(feature_summary(row),
            'Compras: No | Cantidad: 0 | Antebets: Sin datos')

    def test_belatra_vip_wager_is_antebet_keeps_three_purchases(self):
        row = {'provider': 'belatra', 'discovered_modes': [
            {'id': 'SPIN', 'kind': 'SPIN'},
            {'id': 'BELATRA_START_SELECTOR_MATRIX', 'kind': 'CHOICE_BRANCH',
             'observed': True, 'dimensions': [{'field': 'vipOn', 'values': [0, 1]}]},
            {'id': 'BELATRA_BUY_BONUS', 'kind': 'PURCHASE_BRANCH',
             'required_options': ['0', '1', '2']}]}
        self.assertEqual(feature_summary(row), 'Compras: Sí | Cantidad: 3 | Antebets: Sí')

    def test_belatra_math_selector_is_not_antebet(self):
        row = {'provider': 'belatra', 'discovered_modes': [
            {'id': 'SPIN', 'kind': 'SPIN'},
            {'id': 'BELATRA_START_SELECTOR_MATRIX', 'kind': 'CHOICE_BRANCH',
             'dimensions': [{'field': 'mathType', 'values': [0, 1]}]}]}
        self.assertEqual(feature_summary(row), 'Compras: No | Cantidad: 0 | Antebets: No')

    def test_chance_wager_is_antebet_not_purchase(self):
        row = {'provider': 'bgaming', 'discovered_modes': [
            {'id': 'SPIN', 'kind': 'SPIN'},
            {'id': 'PURCHASE_FREESPIN_CHANCE', 'kind': 'PURCHASE'},
            {'id': 'PURCHASE_FREESPIN_BUY', 'kind': 'PURCHASE'}]}
        self.assertEqual(feature_summary(row), 'Compras: Sí | Cantidad: 1 | Antebets: Sí')

    def test_internal_bonus_choices_do_not_add_purchases(self):
        row = {'discovered_modes': [
            {'id': 'PURCHASE_1', 'kind': 'PURCHASE'},
            {'id': 'PURCHASE_1_BONUS_PICK_abc', 'kind': 'CHOICE_BRANCH', 'origin_mode_id': 'PURCHASE_1'},
            {'id': 'PURCHASE_1_FSO', 'kind': 'CHOICE_BRANCH'},
            {'id': 'ANTE_BET_1_BONUS_PICK_abc', 'kind': 'CHOICE_BRANCH'}]}
        self.assertEqual(feature_summary(row), 'Compras: Sí | Cantidad: 1 | Antebets: No')

    def test_disabled_purchase_is_not_available(self):
        row = {'discovered_modes': [
            {'id': 'SPIN', 'kind': 'SPIN'},
            {'id': 'PURCHASE_1', 'kind': 'PURCHASE', 'enabled': False}]}
        self.assertEqual(feature_summary(row), 'Compras: No | Cantidad: 0 | Antebets: No')

    def test_counts_distinct_purchases_not_repeated_attempts(self):
        row = {'discovered_modes': [
            {'id': 'PURCHASE_1', 'kind': 'PURCHASE'},
            {'id': 'PURCHASE_1', 'kind': 'PURCHASE'},
            {'id': 'PURCHASE_2', 'kind': 'PURCHASE'},
            {'id': 'ANTE_BET_1', 'kind': 'ANTE_BET'}],
            'attempts': [{'mode_id': 'PURCHASE_1', 'mode_kind': 'PURCHASE'}] * 3}
        self.assertEqual(feature_summary(row), 'Compras: Sí | Cantidad: 2 | Antebets: Sí')

    def test_missing_discovery_does_not_mean_no_features(self):
        self.assertEqual(feature_summary({}), 'Compras: Sin datos | Cantidad: Sin datos | Antebets: Sin datos')
        self.assertEqual(feature_summary({'discovered_modes': [{'id': 'SPIN', 'kind': 'SPIN'}]}),
                         'Compras: No | Cantidad: 0 | Antebets: No')

    def test_advertised_only_is_not_confirmed_purchase(self):
        row = {'discovered_modes': [{'id': 'PURCHASE_X', 'kind': 'DISCOVERED_ONLY',
                                    'observed': False, 'executable': False}]}
        self.assertEqual(feature_summary(row), 'Compras: Sin datos | Cantidad: Sin datos | Antebets: Sin datos')

    def test_groups_all_results_including_ok_games_by_provider(self):
        rows = [{'provider': p, 'game_name': name, 'discovered_modes': modes}
                for p, name, modes in [('rubyplay', 'Game B', []),
                    ('pragmatic', 'Game A', [{'id': 'PURCHASE_0', 'kind': 'PURCHASE'}])]]
        text = '\n'.join(provider_summary_lines(rows))
        self.assertIn('pragmatic', text)
        self.assertIn('Game A: Compras: Sí | Cantidad: 1 | Antebets: No', text)
        self.assertIn('rubyplay', text)
        self.assertIn('Game B: Compras: Sin datos', text)

    def test_purchase_branch_counts_required_options(self):
        row = {'discovered_modes': [{'id': 'BELATRA_BUY', 'kind': 'PURCHASE_BRANCH',
                                    'required_options': ['0', '1']}]}
        self.assertEqual(feature_summary(row), 'Compras: Sí | Cantidad: 2 | Antebets: No')
