import unittest
from tester_spin.feature_summary import feature_table_counts
class CountsTests(unittest.TestCase):
 def test_authoritative_zero_and_numeric_counts(self):
  self.assertEqual(feature_table_counts({'feature_domains':{'purchase':{'complete':True,'source':'init','options':[]},'ante':{'complete':True,'source':'init','options':[]}}}),(0,0))
  self.assertEqual(feature_table_counts({'feature_domains':{'purchase':{'complete':True,'source':'init','options':['a','b']},'ante':{'complete':True,'source':'init','options':['x','y','z']}}}),(2,3))
 def test_unknown_is_not_false_absence(self):
  self.assertEqual(feature_table_counts({}),(None,None))
 def test_observed_options_without_total_and_continuations(self):
  modes=[{'id':'BUY_X','kind':'PURCHASE'},{'id':'ANTE_BET_X','kind':'ANTE_BET'},{'id':'FOLLOW','kind':'CONTINUATION','origin_mode_id':'BUY_X'}]
  self.assertEqual(feature_table_counts({'discovered_modes':modes}),(1,1))
