import importlib.util
from pathlib import Path
import unittest
from tester_spin import feature_summary as m
class SummaryTests(unittest.TestCase):
 def test_internal_buy_is_unconfirmed(self):
  r={'provider':'redtiger','discovered_modes':[{'id':'SPIN','kind':'SPIN'},{'id':'PURCHASE_FREESPINS','kind':'PURCHASE','observed':True,'feature_buy':'FreeSpins'}]}
  self.assertEqual(m.feature_summary(r),'Compras: Sin datos | Cantidad: Sin datos | Antebets: No')
 def test_normal_spin_never_counts_as_purchase(self):
  r={'provider':'redtiger','discovered_modes':[{'id':'SPIN','kind':'SPIN','feature_buy':'FreeSpins'}]}
  self.assertEqual(m.feature_summary(r),'Compras: No | Cantidad: 0 | Antebets: No')
 def test_client_confirmed_buy_counts(self):
  r={'provider':'redtiger','discovered_modes':[{'id':'SPIN','kind':'SPIN'},{'id':'PURCHASE_FREESPINS','kind':'PURCHASE','client_observed':True}]}
  self.assertIn('Compras: Sí | Cantidad: 1',m.feature_summary(r))
if __name__=='__main__':unittest.main()
