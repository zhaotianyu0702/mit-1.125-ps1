import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('geo_screen', Path(__file__).resolve().parents[1] / 'scripts/collect-public-boards.py')
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)

class GeographyTests(unittest.TestCase):
    def test_full_state_names_extend_coverage(self):
        states = {r['state'] for r in screen.locations('Las Vegas, Nevada, United States; Newark, New Jersey, United States')}
        self.assertEqual(states, {'NV', 'NJ'})

    def test_dc_does_not_add_washington_state(self):
        self.assertEqual({r['state'] for r in screen.locations('Washington, DC')}, {'DC'})

    def test_west_virginia_does_not_add_virginia(self):
        self.assertEqual({r['state'] for r in screen.locations('West Virginia, United States')}, {'WV'})
