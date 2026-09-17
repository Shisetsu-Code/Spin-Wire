import json,tempfile,unittest
from pathlib import Path
from tester_spin.manual_review import review_item,render_review

class ReviewEvidenceTests(unittest.TestCase):
    def case(self,root):
        (root/'server-observations.json').write_text(json.dumps({'observations':[{'review_required':True,'classification':'NEW_RESPONSE'}]}))
        (root/'run-tree.json').write_text(json.dumps({'trajectories':[{'attempt':1,'reported_ok':True,'reported_terminal':True,'gaps':[],
            'return_to_base':{'status':'CONFIRMED','consecutive_base':2,'connection_reused':True}}]}))
        return dict(provider='bgaming',slug='x',game_name='Example',status='OK',run_dir=str(root),attempts=[{'number':1,'ok':True,'terminal':True}])

    def test_completed_novel_response_is_not_unfinished_action(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(review_item(self.case(Path(d))))

    def test_unparsed_response_stays_reviewable_despite_completion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);row=self.case(root)
            (root/'server-observations.json').write_text(json.dumps({'unparsed':1}))
            self.assertIsNotNone(review_item(row))

    def test_advertised_only_is_uncertain_availability_not_missing_purchase(self):
        with tempfile.TemporaryDirectory() as d:
            row=self.case(Path(d));row.update(status='PARCIAL',error='BGaming compras anunciadas sin wire cliente demostrado: PURCHASE_BONUS_BUY.',
                discovered_modes=[{'id':'PURCHASE_BONUS_BUY','kind':'DISCOVERED_ONLY','client_observed':False,'executable':False,'coverage_required':False,'evidence_level':'SERVER_ADVERTISED'}])
            item=review_item(row)
            self.assertEqual(item['category'],'availability')
            text=render_review([row])
            self.assertNotIn('Hay compras o apuestas especiales pendientes',text)
            self.assertIn('DISPONIBILIDAD SIN CONFIRMAR',text)
            self.assertNotIn('Capturar cada compra',text)

    def test_confirmed_choice_gap_is_still_required(self):
        with tempfile.TemporaryDirectory() as d:
            row=self.case(Path(d));row['discovered_modes']=[{'id':'PURCHASE_PICK','coverage_required':True,'required_options':['0','1'],'covered_options':['0']}]
            self.assertIsNotNone(review_item(row))

    def test_missing_proof_does_not_suppress_novelty(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);row=self.case(root);(root/'run-tree.json').write_text(json.dumps({'trajectories':[]}))
            self.assertIsNotNone(review_item(row))

    def test_same_attempt_number_in_different_modes_uses_its_own_proof(self):
        from tester_spin.manual_review import _completed_attempts
        attempts=[{'number':1,'mode_id':m,'ok':True,'terminal':True} for m in ('SPIN','BUY')]
        paths=[{'attempt':1,'origin':{'mode_id':m},'reported_ok':True,'reported_terminal':True,
            'return_to_base':{'status':'CONFIRMED','consecutive_base':2,'connection_reused':True}} for m in ('SPIN','BUY')]
        self.assertTrue(_completed_attempts(attempts,paths))
        paths[0]['return_to_base']['status']='REVIEW_REQUIRED'
        self.assertFalse(_completed_attempts(attempts,paths))
