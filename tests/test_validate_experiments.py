import unittest

from src.validate_experiments import evaluate


def scenario(mode, priority, name):
    return {'mode': mode, 'steps': 600, 'pedestrians_enabled': True,
            'pedestrian_demand': 'high', 'pedestrian_priority_enabled': priority,
            'run_id': name, 'completed_vehicle_trips': 310,
            'average_vehicle_waiting_seconds': 15.27,
            'observed_pedestrian_crossing_starts': 176,
            'observed_pedestrian_crossing_completions': 173,
            'average_pre_crossing_wait_seconds': 0.91,
            'pedestrian_priority_adjustments': 11 if priority else 0,
            'pedestrian_wait_alerts': 0,
            'green_adjustments': 19 if mode == 'adaptive' else 0}


class ExperimentValidationTest(unittest.TestCase):
    def setUp(self):
        self.runs = [scenario('adaptive', True, 'adaptive-priority'),
                     scenario('adaptive', False, 'adaptive-no-priority'),
                     scenario('fixed', False, 'fixed')]

    def test_valid_three_scenarios(self):
        self.assertTrue(evaluate(self.runs)['passed'])

    def test_missing_scenario_is_failure(self):
        self.assertFalse(evaluate(self.runs[:2])['passed'])

    def test_illegal_fixed_adjustment_is_failure(self):
        self.runs[2]['green_adjustments'] = 1
        self.assertFalse(evaluate(self.runs)['passed'])

    def test_more_completions_than_starts_is_failure(self):
        self.runs[0]['observed_pedestrian_crossing_completions'] = 177
        self.assertFalse(evaluate(self.runs)['passed'])


if __name__ == '__main__':
    unittest.main()
