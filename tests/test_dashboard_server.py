import json
import tempfile
import unittest
from pathlib import Path

from src.server import high_demand_comparison, load_runs


class DashboardDataTest(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(load_runs(Path(folder)), [])

    def test_skips_invalid_and_selects_three_scenarios(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / 'broken.metrics.json').write_text('{invalido', encoding='utf-8')
            cases = [('fixed-20261117T100000', 'fixed', False),
                     ('adaptive-20261117T100001', 'adaptive', False),
                     ('adaptive-20261117T100002', 'adaptive', True)]
            for name, mode, priority in cases:
                (target / (name + '.metrics.json')).write_text(json.dumps({
                    'mode': mode, 'steps': 600, 'pedestrians_enabled': True,
                    'pedestrian_demand': 'high', 'pedestrian_priority_enabled': priority,
                    'average_vehicle_waiting_seconds': 20
                }), encoding='utf-8')
            runs = load_runs(target)
            self.assertEqual(len(runs), 3)
            self.assertEqual(set(high_demand_comparison(runs)),
                             {'adaptive_priority', 'adaptive_no_priority', 'fixed'})

    def test_different_demands_not_compared(self):
        runs = [{'mode': 'fixed', 'steps': 600, 'pedestrians_enabled': True,
                 'pedestrian_demand': 'normal', 'pedestrian_priority_enabled': False}]
        self.assertEqual(high_demand_comparison(runs), {})


if __name__ == '__main__':
    unittest.main()
